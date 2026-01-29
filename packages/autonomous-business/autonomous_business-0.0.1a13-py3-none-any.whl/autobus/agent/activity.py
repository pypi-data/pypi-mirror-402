import sqlite3
from importlib import resources as impresources
from temporalio import activity, workflow
from autobus import prolog_template
from pathlib import Path
from autobus.config import config


@activity.defn
async def get_config(section:str, name:str) -> str:
    """
    Get config[section][config_name]
    """
    return config[section][name]

@activity.defn
async def get_prolog_template(template_name:str) -> str:
    """
    Given a template name, return the Prolog template.
    """
    template = impresources.read_text(prolog_template, template_name)
    return template


@activity.defn
async def get_db_schema(db_path:str=config['directory']['db_file_path']) -> str:
    """
    Return the schema of the database as DDL statements (CREATE TABLE/INDEX/etc.).
    The result is a single string containing all DDL statements separated by blank lines.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all user-defined schema objects (tables, indexes, views, triggers),
    # skipping SQLite's internal tables
    cursor.execute("""
        SELECT type, name, sql
        FROM sqlite_master
        WHERE name NOT LIKE 'sqlite_%'
          AND sql IS NOT NULL
        ORDER BY type, name
    """)

    statements = []
    for obj_type, name, sql in cursor.fetchall():
        # Ensure each statement ends with a semicolon
        sql = sql.strip()
        if not sql.endswith(";"):
            sql += ";"
        statements.append(sql)

    conn.close()

    return "\n\n".join(statements)

@activity.defn
async def save_text_to_file(text:str, filepath:str, encoding:str="utf-8") -> None:
    """
    Save the given text to a file.

    :param text: The text content to write.
    :param filepath: Path to the file to write.
    :param encoding: Text encoding (default: 'utf-8').
    """

    Path(filepath).parent.mkdir(exist_ok=True)

    with open(filepath, "w", encoding=encoding) as f:
        f.write(text)
