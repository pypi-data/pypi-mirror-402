"""PNG diagram exporter for dbt-conceptual using Playwright."""

import asyncio
import tempfile
from pathlib import Path
from typing import BinaryIO

from dbt_conceptual.state import ProjectState


def export_png(state: ProjectState, output: BinaryIO) -> None:
    """Export conceptual model as PNG diagram by screenshotting the web UI canvas.

    Uses Playwright to start a headless server, load the canvas view, and capture
    a screenshot. This ensures the PNG export matches the visual style of the
    interactive UI.

    Args:
        state: The conceptual model state
        output: Binary output stream for PNG file

    Raises:
        ImportError: If playwright is not installed
        RuntimeError: If screenshot capture fails
    """
    try:
        import playwright  # noqa: F401
    except ImportError as err:
        raise ImportError(
            "PNG export requires Playwright for headless browser automation.\n"
            "Install with: pip install playwright && playwright install chromium"
        ) from err

    # Run async screenshot in sync context
    png_data = asyncio.run(_capture_canvas_screenshot(state))
    output.write(png_data)


async def _capture_canvas_screenshot(state: ProjectState) -> bytes:
    """Capture screenshot of canvas using Playwright.

    Args:
        state: The conceptual model state

    Returns:
        PNG image bytes
    """
    import threading
    import time

    from playwright.async_api import async_playwright

    # Create temporary conceptual.yml file
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        models_dir = tmpdir_path / "models" / "conceptual"
        models_dir.mkdir(parents=True)

        # Write conceptual.yml
        conceptual_file = models_dir / "conceptual.yml"
        _write_state_to_yaml(state, conceptual_file)

        # Create minimal dbt_project.yml
        dbt_project = tmpdir_path / "dbt_project.yml"
        dbt_project.write_text(
            "name: temp_export\n"
            "version: 1.0.0\n"
            "config-version: 2\n"
            "model-paths: ['models']\n"
        )

        # Start Flask server in background thread
        from dbt_conceptual.server import create_app

        app = create_app(tmpdir_path)

        server_thread = threading.Thread(
            target=lambda: app.run(host="127.0.0.1", port=5555, debug=False),
            daemon=True,
        )
        server_thread.start()

        # Wait for server to start
        time.sleep(2)

        # Capture screenshot with Playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={"width": 1400, "height": 900})

            # Load canvas view
            await page.goto("http://127.0.0.1:5555/")

            # Wait for canvas to render
            await page.wait_for_selector("canvas", timeout=10000)
            await page.wait_for_timeout(1000)  # Additional time for layout

            # Take screenshot of canvas element
            canvas = await page.query_selector("canvas")
            if canvas:
                screenshot_bytes = await canvas.screenshot(omit_background=False)
            else:
                # Fallback: screenshot entire viewport
                screenshot_bytes = await page.screenshot(full_page=False)

            await browser.close()

            return screenshot_bytes


def _write_state_to_yaml(state: ProjectState, output_path: Path) -> None:
    """Write ProjectState back to YAML format.

    Args:
        state: The project state to write
        output_path: Path to write YAML file
    """
    import yaml

    data: dict = {"version": 1}

    # Write domains
    if state.domains:
        data["domains"] = {}
        for domain_id, domain in state.domains.items():
            data["domains"][domain_id] = {
                "name": domain.display_name,
            }

    # Write concepts
    if state.concepts:
        data["concepts"] = {}
        for concept_id, concept in state.concepts.items():
            concept_data: dict = {
                "name": concept.name,
            }
            if concept.domain:
                concept_data["domain"] = concept.domain
            if concept.owner:
                concept_data["owner"] = concept.owner
            if concept.definition:
                concept_data["definition"] = concept.definition
            if concept.status and concept.status != "complete":
                concept_data["status"] = concept.status

            data["concepts"][concept_id] = concept_data

    # Write relationships
    if state.relationships:
        data["relationships"] = []
        for _rel_id, rel in state.relationships.items():
            rel_data: dict = {
                "name": rel.name,
                "from": rel.from_concept,
                "to": rel.to_concept,
            }
            if rel.cardinality:
                rel_data["cardinality"] = rel.cardinality
            if rel.definition:
                rel_data["definition"] = rel.definition
            if rel.status and rel.status != "complete":
                rel_data["status"] = rel.status

            data["relationships"].append(rel_data)

    output_path.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))
