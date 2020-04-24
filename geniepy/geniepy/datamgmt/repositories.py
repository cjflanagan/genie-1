"""Data Access Repositories to abstract interation with databases."""
from typing import Generator
from abc import ABC, abstractmethod
import pandas as pd
from pandas import DataFrame
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, Float, String
from google.oauth2 import service_account
import pandas_gbq
import geniepy
from geniepy.errors import DaoError


CTD_TABLE_NAME = "ctd"
"""Name of ctd source table."""
CTD_DAO_TABLE = Table(
    CTD_TABLE_NAME,
    MetaData(),
    # No primary key allows duplicate records
    Column("digest", String, primary_key=False, nullable=False),
    Column("genesymbol", String),
    Column("geneid", Integer, nullable=False),
    Column("diseasename", String),
    Column("diseaseid", String, nullable=False),
    Column("pmids", String, nullable=False),
)
"""CTD DAO Repository Schema."""

PUBMED_TABLE_NAME = "pubmed"
"""Name of pubmed source table."""
PUBMED_DAO_TABLE = Table(
    PUBMED_TABLE_NAME,
    MetaData(),
    # No primary key allows duplicate records
    Column("pmid", Integer, primary_key=False, nullable=False),
    Column("date_completed", String),
    Column("pub_model", String),
    Column("title", String),
    Column("iso_abbreviation", String),
    Column("article_title", String),
    Column("abstract", String),
    Column("authors", String),
    Column("language", String),
    Column("chemicals", String),
    Column("mesh_list", String),
)
"""PUBMED DAO Repository Schema."""


CLSFR_TABLE_NAME = "classifier"
"""Name of geniepy classifier output table."""
CLSFR_DAO_TABLE = Table(
    CLSFR_TABLE_NAME,
    MetaData(),
    # No primary key allows duplicate records
    Column("digest", String, primary_key=False, nullable=False),
    Column("pub_score", Float, nullable=False),
    Column("ct_score", Float, nullable=False),
)
"""Classifier Output DAO Repository Schema."""


class BaseRepository(ABC):
    """Base Abstract Class for Data Access Object Repositories."""

    __slots__ = ["_table", "_tablename"]

    @property
    def tablename(self):
        """Return DAO repo's tablename."""
        return self._tablename  # pylint: disable=E1101

    @abstractmethod
    def save(self, payload: DataFrame):
        """
        Save payload to database table.

        Arguments:
            payload {DataFrame} -- the payload to be stored in db

        Raises:
            DaoError: if cannot save payload to db
        """

    @abstractmethod
    def delete_all(self):
        """Delete all records in repository."""

    @abstractmethod
    # pylint: disable=bad-continuation
    def query(
        self, query: str = None, chunksize: int = geniepy.CHUNKSIZE
    ) -> Generator[DataFrame, None, None]:
        """
        Query DAO repo and returns a generator of DataFrames with query results.

        Keyword Arguments:
            query {str} -- Query string. (default: {None} returns all values)
            chunksize {int} -- Number of rows of dataframe per chunk (default: {10e3})

        Returns:
            Generator[DataFrame] -- Generator to iterate over DataFrame results.
        """


class SqlRepository(BaseRepository):
    """Implementation of Sqlite Data Access Object Repository."""

    __slots__ = ["_engine"]

    def __init__(self, db_loc: str, tablename: str, table: Table):
        """
        Initialize DAO repository and create table.

        Arguments:
            db_loc {str} -- location of underlying database
            tablename {str} -- the dao table name
            schema {Table} -- the table schema
        """
        self._tablename = tablename
        self._table = table
        # Create sql engine
        self._engine = create_engine(db_loc)
        # Create Table
        self._table.create(self._engine)

    def save(self, payload: DataFrame):
        """
        Save payload to database table.

        Arguments:
            payload {DataFrame} -- the payload to be stored in db

        Raises:
            DaoError: if cannot save payload to db
        """
        try:
            payload.to_sql(
                self._tablename,
                con=self._engine,
                if_exists="append",
                index=False,
                method="multi",
            )
        except Exception as sql_exp:
            raise DaoError(sql_exp)

    def delete_all(self):
        """Delete all records in repository."""
        self._table.drop(self._engine)
        self._table.create(self._engine)

    # pylint: disable=bad-continuation
    def query(
        self, query: str = None, chunksize: int = geniepy.CHUNKSIZE
    ) -> Generator[DataFrame, None, None]:
        """
        Query DAO repo and returns a generator of DataFrames with query results.

        Keyword Arguments:
            query {str} -- Query string. (default: {None} returns all values)
            chunksize {int} -- Number of rows of dataframe per chunk (default: {10e3})

        Returns:
            Generator[DataFrame] -- Generator to iterate over DataFrame results.
        """
        if query is None:
            return pd.read_sql(self._tablename, con=self._engine, chunksize=chunksize)
        # If query string provided
        generator = pd.read_sql_query(query, self._engine, chunksize=chunksize)
        return generator


class GbqRepository(BaseRepository):
    """Implementation of Sqlite Data Access Object Repository."""

    __slots__ = ["_proj", "_credentials"]

    def __init__(
        self, db_loc: str, tablename: str, table: Table, credentials_path: str
    ):
        """
        Initialize DAO repository and create table.

        Arguments:
            db_loc {str} -- name of BigQuery project
            tablename {str} -- the dao table name including dataset (i.e. test.table)
            schema {Table} -- the table schema
            credentials_path {str} -- path to gcp credentials json
        """
        self._tablename = tablename
        self._table = table
        self._proj = db_loc
        # self._credentials = service_account.Credentials.from_service_account_file(
        # credentials_path,
        # )
        # pandas_gbq.context.credentials = self._credentials
        # pandas_gbq.context.project = self._proj

    def save(self, payload: DataFrame):
        """
        Save payload to database table.

        Arguments:
            payload {DataFrame} -- the payload to be stored in db

        Raises:
            DaoError: if cannot save payload to db
        """
        # try:
        #     payload.to_sql(
        #         self._tablename,
        #         con=self._engine,
        #         if_exists="append",
        #         index=False,
        #         method="multi",
        #     )
        # except Exception as sql_exp:
        #     raise DaoError(sql_exp)
        raise NotImplementedError

    def delete_all(self):
        """Delete all records in repository."""
        # self._table.drop(self._engine)
        # self._table.create(self._engine)
        raise NotImplementedError

    # pylint: disable=bad-continuation
    def query(
        self, query: str = None, chunksize: int = geniepy.CHUNKSIZE
    ) -> Generator[DataFrame, None, None]:
        """
        Query DAO repo and returns a generator of DataFrames with query results.

        Keyword Arguments:
            query {str} -- Query string. (default: {None} returns all values)
            chunksize {int} -- Number of rows of dataframe per chunk (default: {10e3})

        Returns:
            Generator[DataFrame] -- Generator to iterate over DataFrame results.
        """
        # if query is None:
        #     return pd.read_sql(self._tablename, con=self._engine, chunksize=chunksize)
        # # If query string provided
        # generator = pd.read_sql_query(query, self._engine, chunksize=chunksize)
        # return generator
        raise NotImplementedError
