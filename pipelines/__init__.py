"""Offline pipelines: dataset generation, ingestion/scraping and model training.

Not part of the deployed runtime (``api.main``). These modules are dev/CI tooling
that produces the artifacts the product consumes (scored CSV, trained models).
They may depend on ``src`` (domain), never the other way around.
"""
