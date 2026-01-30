import math
import os
import subprocess
import tempfile
from typing import Any, Dict, List, Optional

import numpy as np
import pyproj
import rasterio as rio
import snappy
import typer
from dateutil import parser
from rasterio.windows import from_bounds
from rich import print
from rich.progress import (
    BarColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

from ...exceptions import (
    CollectionAlreadyExistsError,
    CollectionNotFoundError,
    CommandPermissionError,
    CreateDatasetError,
    DatasetAlreadyExistsError,
    GetTaskError,
    InvalidProductError,
)
from ...helper.decorators import require_api_key


class IngestionMixin:
    """Data ingestion and visualization operations."""
    
    @require_api_key
    async def create_pyramids(
        self,
        name: str,
        levels: int,
        config: Dict[str, Any],
        collection: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create pyramid tiles for a dataset.

        Args:
            name: Dataset name
            levels: Maximum zoom level for pyramid (e.g., 8)
            config: Dictionary of configuration key-value pairs
            collection: Name of collection (optional, defaults to "{name}-pyramids")

        Returns:
            API response with task_id

        Raises:
            GetTaskError: If the API request fails
            CollectionNotFoundError: If the collection is not found
            CreateCollectionError: If collection creation fails
        """
        if collection is None or collection == "":
            collection = f"{name}-pyramids"
            try:
                await self.create_collection(collection=collection)
            except CollectionAlreadyExistsError:
                # Collection already exists, continue with it
                pass
        else:
            try:
                await self.get_collection(collection=collection)
            except CollectionNotFoundError:
                await self.create_collection(collection=collection)

        pyramid_request = {
            'collection_name': collection,
            'name': name,
            'max_zoom': levels,
            **config
        }

        response, status = await self._client._terrakio_request(
            "POST",
            "tasks/pyramids",
            json=pyramid_request
        )

        if status != 200:
            if status == 400:
                raise InvalidProductError(
                    f"Pyramid creation failed with status {status}: {response}", 
                    status_code=status
                )
            raise GetTaskError(
                f"Pyramid creation failed with status {status}: {response}", 
                status_code=status
            )
        
        task_id = response["task_id"]
        await self.track_progress(task_id)

        return {"task_id": task_id}

    @require_api_key
    async def tif(
        self,
        file: str,
        dataset: str,
        product: List[str],
        bucket: str,
        path: str,
        no_data: float,
        max_zoom: int,
        date: str,
        add_config: bool = True,
        generate_pyramids: bool = True,
        geot: Optional[List[float]] = None,
        no_interactive: bool = False,
        tile_size: int = 400,
        update_config: bool = True,
    ) -> Dict[str, Any]:
        """
        Ingest a tif file and optionally generate pyramids.

        Args:
            file: Path to the tif file to ingest
            dataset: Dataset name
            product: List of product names
            bucket: Storage bucket
            path: Storage path
            no_data: No data value
            max_zoom: Maximum zoom level
            date: Date string
            add_config: Add dataset configuration (default: True)
            generate_pyramids: Generate pyramids after ingestion (default: True)
            geot: Geotransform parameters (optional)
            no_interactive: Non-interactive mode (default: False)
            tile_size: Size of tiles (default: 400)
            update_config: Update config with new date (default: True)

        Returns:
            API response with task_id

        Raises:
            GetTaskError: If the API request fails
        """
        with rio.open(file) as src:
            if len(product) != src.meta["count"]:
                print("[bold red]Products don't match number of bands[/bold red]")
                raise typer.Exit(code=2)
            meta = src.meta
            dtype = meta["dtype"]
            transform = meta["transform"]
            if not geot:
                geot = [transform[2], transform[0], transform[1], transform[5], transform[3], transform[4]]
            x0, y0 = geot[0], geot[3]
            proj = pyproj.Proj(meta["crs"])

            j_max = int(math.ceil(meta['height'] / tile_size))
            i_max = int(math.ceil(meta['width'] / tile_size))

            if add_config:
                try:
                    await self._client.datasets.create_dataset(
                        name=dataset,
                        products=product,
                        dates_iso8601=[date],
                        bucket=bucket,
                        path=f"{path}/%s_%s_%03d_%03d_%02d.snp",
                        data_type=dtype,
                        no_data=no_data,
                        i_max=i_max,
                        j_max=j_max,
                        y_size=tile_size,
                        x_size=tile_size,
                        proj4=proj.definition_string(),
                        abstract="",
                        geotransform=geot,
                        max_zoom=0,
                    )
                    print(f"[green]Added dataset [bold yellow]{dataset}[/bold yellow]![/green]")
                except CommandPermissionError:
                    print("[bold red]You do not have the right permissions![/bold red]")
                    raise typer.Exit(code=1)
                except DatasetAlreadyExistsError:
                    if not no_interactive:
                        typer.confirm(f"Dataset '{dataset}' already exists. Do you want to update it?", abort=True)
                    await self._client.datasets.overwrite_dataset(
                        name=dataset,
                        products=product,
                        dates_iso8601=[date],
                        bucket=bucket,
                        path=f"{path}/%s_%s_%03d_%03d_%02d.snp",
                        data_type=dtype,
                        no_data=no_data,
                        i_max=i_max,
                        j_max=j_max,
                        y_size=tile_size,
                        x_size=tile_size,
                        proj4=proj.definition_string(),
                        abstract="",
                        geotransform=geot,
                        max_zoom=0,
                    )
                    print(f"[green]Updated dataset [bold yellow]{dataset}[/bold yellow]![/green]")
                except CreateDatasetError as e:
                    print(f"[bold red]{e.status_code} Error adding data[/bold red]")
                    raise typer.Exit(code=1)
            else:
                if not no_interactive and update_config:
                    await self._client.datasets.update_dataset(
                        name=dataset,
                        append=True,
                        dates_iso8601=[date]
                    )
    
            with tempfile.TemporaryDirectory() as tmpdirname:
                progress = Progress(
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TaskProgressColumn(),
                    TimeElapsedColumn(),
                )
                
                with progress:
                    task = progress.add_task(description="[bold green]Writing tiles...[/bold green]", total=j_max*i_max)
                    for j in range(0, j_max+1):
                        for i in range(0, i_max+1):
                            left = x0 + i*tile_size*geot[1]
                            right = x0 + (i+1)*tile_size*geot[1]
                            top = y0 - j*tile_size*geot[1]
                            bottom = y0 - (j+1)*tile_size*geot[1]

                            data = src.read(window=from_bounds(left, bottom, right, top, src.transform), boundless=True, masked=True)
                            for band in range(src.meta["count"]):
                                out = data[band]
                                if np.ma.is_masked(out) and out.mask.all():
                                    progress.update(task, advance=1)
                                    continue

                                out = out.filled(no_data)
                                out_bytes = out.tobytes()
                                
                                date_obj = parser.parse(date)
                                with open(f"{tmpdirname}/{product[band]}_{date_obj.strftime('%Y%m%d%H%M%S')}_{i:03d}_{j:03d}_00.snp", 'wb') as f:
                                    comp = snappy.compress(out_bytes)
                                    f.write(comp)
                                progress.update(task, advance=1)
                upload_progress = Progress(
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(pulse_style="green"),
                    TimeElapsedColumn(),
                )
                with upload_progress:
                    upload_progress.add_task(description="[bold green]Uploading tiles...[/bold green]", total=None)
                    subprocess.run(
                        ["gsutil", "-m", "cp", "-r", "*", f"gs://{bucket}/{path}"],
                        cwd=f"{tmpdirname}",
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )

        if generate_pyramids:
            await self.create_pyramids(
                name=dataset,
                levels=max_zoom,
                config={
                    "products": product,
                    "dates_iso8601": [date if date.endswith("Z") else date + "Z"],
                    "bucket": bucket,
                    "path": f"{path}/%s_%s_%03d_%03d_%02d.snp",
                    "data_type": dtype,
                    "i_max": i_max,
                    "j_max": j_max,
                    "x_size": tile_size,
                    "y_size": tile_size,
                    "proj4": proj.definition_string(),
                    "geotransform": geot,
                    "no_data": no_data,
                }
            )