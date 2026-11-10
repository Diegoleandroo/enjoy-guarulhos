"""Erros de negócio. Não sabem nada de HTTP: o adaptador traduz para 404/409/422."""


class ErroDeNegocio(Exception):
    pass


class NaoEncontrado(ErroDeNegocio):
    pass


class DadosInvalidos(ErroDeNegocio):
    pass


class Conflito(ErroDeNegocio):
    pass
