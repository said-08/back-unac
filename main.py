from typing import Annotated, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Session, SQLModel, create_engine, select


class Usuario(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(index=True)
    email: str = Field(index=True, unique=True)
    edad: Optional[int] = Field(default=None)
    direccion: Optional[str] = Field(default=None)


sqlite_file_name = "usuarios.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]

app = FastAPI()


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.post("/usuarios/")
def create_usuario(usuario: Usuario, session: SessionDep) -> Usuario:
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario


@app.get("/usuarios/")
def read_usuarios(
    session: SessionDep,
    offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,
) -> list[Usuario]:
    usuarios = session.exec(select(Usuario).offset(offset).limit(limit)).all()
    return usuarios


@app.get("/usuarios/{usuario_id}")
def read_usuario(usuario_id: int, session: SessionDep) -> Usuario:
    usuario = session.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario


@app.delete("/usuarios/{usuario_id}")
def delete_usuario(usuario_id: int, session: SessionDep):
    usuario = session.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    session.delete(usuario)
    session.commit()
    return {"ok": True}
