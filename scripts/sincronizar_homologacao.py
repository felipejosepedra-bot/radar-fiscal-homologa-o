#!/usr/bin/env python3
"""Atualiza somente os dois acervos publicos da homologacao a partir da producao.

Nao acessa credenciais, nao altera o codigo HTML e nao escreve no repositorio oficial.
"""
import argparse
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://raw.githubusercontent.com/felipejosepedra-bot/radar-fiscal/main/"
ACERVOS = {
    "atualizacoes.json": "atualizacoes",
    "relatorios.json": "relatorios",
}

def baixar(nome):
    request = Request(
        BASE_URL + nome,
        headers={"User-Agent": "radar-fiscal-homologacao/1.0", "Cache-Control": "no-cache"},
    )
    with urlopen(request, timeout=30) as response:
        content = response.read().decode("utf-8")
    return content

def validar(nome, conteudo, campo):
    objeto = json.loads(conteudo)
    itens = objeto.get(campo) if isinstance(objeto, dict) else None
    if not isinstance(itens, list) or not itens:
        raise ValueError(f"Acervo invalido ou vazio: {nome} / {campo}")
    return len(itens)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--github-output")
    args = p.parse_args()

    # Baixe e valide tudo antes de modificar qualquer arquivo.
    atualizados = {}
    for nome, campo in ACERVOS.items():
        novo = baixar(nome)
        quantidade = validar(nome, novo, campo)
        arquivo = ROOT / nome
        antigo = arquivo.read_text(encoding="utf-8") if arquivo.exists() else ""
        if antigo:
            quantidade_antiga = validar(nome, antigo, campo)
            if quantidade < quantidade_antiga:
                raise ValueError(
                    f"{nome}: producao tem menos registros ({quantidade}) do que "
                    f"homologacao ({quantidade_antiga}); revisao manual necessaria"
                )
        if novo != antigo:
            atualizados[nome] = novo
        print(f"{nome}: {quantidade} registros na producao.")

    for nome, conteudo in atualizados.items():
        (ROOT / nome).write_text(conteudo, encoding="utf-8")
    mudou = bool(atualizados)
    if args.github_output:
        with open(args.github_output, "a", encoding="utf-8") as output:
            output.write(f"changed={str(mudou).lower()}\n")
    print("Arquivos sincronizados: " + ", ".join(atualizados) if mudou else "Acervos ja sincronizados.")

if __name__ == "__main__":
    main()
