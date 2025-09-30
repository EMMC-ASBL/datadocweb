# Dataset Editor: a collaborative app to document data

## Key Concepts

1. Multi-Expert Collaboration:
    - Lab experts contribute experimental context and metadata.
    - Knowledge graph experts ensure semantic consistency and ontology
      alignment.
    - Project managers help coordinate and ensure completeness and usability.
2. Unified App for Documentation:
    - Centralized interface to collect and structure the metadata.
    - Could include forms, tables, templates, and validation mechanisms.
    - Prepares data for ingestion into a triple store (via CSV format and
      Tripper library).
3. Dataset Structure:
    - The app can manage multiple dataset.
    - One dataset has a name and a list of tables:
    - Each table has a name, a list of rows, and a list of columns.
    - Each column is defined with a name, a datatype (identifier, text, number,
      choice, etc.), allowed values to define the choices, and a concept name
      (ontology link).
    - A column can be defined as a reference to another table column (e.g. a
      table "Images" as a column "Filename" and a column "Alloy" the choice given in this column "Alloy" is from the table "Alloys" column "Name").
4. Each user (or expert) can modify table cells, define columns. The dataset
   must be validated by the knowledge graph expert (this user will ensure that
   each column has a "concept name").

## Advantages

- The lab experts can use their own vocabulary (we can use "human" label for 
  the column header).
- A discussion must be done with KB expert if a column definition is not clear.
- We can store the definition of a dataset collection as simple JSON or in
  database, and open it again and make modification or enrich the data doccumentation, and send it to triple store.
- We can export a dataset to csv, xlsx, or directly upload to the triple store.
- We can link table by column, like in relationnal database.
- Should be easy-peasy GUI !
- We could have a simple Python script to code the dataset structure proposed
  above, it will be easier to prepare a dataset if large data already exists.
