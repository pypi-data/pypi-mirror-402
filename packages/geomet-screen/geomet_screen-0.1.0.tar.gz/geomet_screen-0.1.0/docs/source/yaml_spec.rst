
YAML Schema Specification
=========================

This page describes the YAML schema for defining screen layouts, panels, and decks, along with validation rules implemented using ``pydantic``.

Schema Overview
---------------

The YAML file consists of two main sections:

- **panels**: Defines reusable panel specifications.
- **screens**: Defines one or more screens, each with metadata and decks.

Example YAML Structure
-----------------------

.. code-block:: yaml

    panels:
      P001:
        width: 500
        height: 300
        material: polyurethane
        image_path: "/path/to/panel_P001.png"
      P002:
        width: 600
        height: 300
        material: rubber

    screens:
      SC001:
        metadata:
          location: "Plant A"
          date: "2026-01-20"
        decks:
          TD:
            rows: 3
            cols: 4
            layout:
              - [P001, P001, P002, P002]
              - [P001, P001, P002, P002]
              - [P001, P001, P002, P002]
          BD:
            rows: 2
            cols: 4
            layout:
              - [P002, P002, P002, P002]
              - [P002, P002, P002, P002]

Validation Rules
----------------

The following validation rules apply:

- **Panels Section**
  - Each panel must define ``width``, ``height``, and ``material``.
  - Optional ``image_path`` must point to an existing file if provided.

- **Screens Section**
  - Each screen must include ``metadata`` and ``decks``.
  - Each deck:
    - ``rows`` and ``cols`` must match the dimensions of ``layout``.
    - All panel IDs in ``layout`` must exist in the ``panels`` section.

- **Global Rules**
  - No duplicate IDs.
