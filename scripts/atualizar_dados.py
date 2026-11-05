"""Copia a aba Livros da planilha para dados/livros.json e guarda as capas em capas/.

Se algo der errado, o arquivo atual fica como está e o site continua com a última versão boa.

Uso:
  python scripts/atualizar_dados.py            lê a planilha indicada em scripts/fonte.json
  python scripts/atualizar_dados.py --csv A    lê um arquivo CSV local, para teste
  python scripts/atualizar_dados.py --forcar   aceita uma queda grande no número de livros
"""
import argparse
import csv
import io
import json
import re
import sys
import unicodedata
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FONTE = RAIZ / "scripts" / "fonte.json"
SAIDA = RAIZ / "dados" / "livros.json"
CAPAS = RAIZ / "capas"

TIPOS = {"Obra autoral": "autoral", "Autoral": "autoral", "Coletânea": "coletanea", "Dissertação ou tese": "tese"}
PRATELEIRAS = {"Professores": "professores", "Alunos e egressos": "alunos"}
OBRIGATORIAS = ["Título", "Autores", "É organização?", "Ano", "Cidade", "Editora",
                "Tipo de obra", "Prateleira", "Sinopse", "Capa"]
EXTENSOES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
LIMITE_CAPA = 5 * 1024 * 1024
AGENTE = "estante-ppgd/1.0"

avisos = []


def avisar(texto):
    avisos.append(texto)
    print("AVISO:", texto)


def parar(texto):
    print("ERRO:", texto, "\nO arquivo de dados não foi alterado.")
    sys.exit(1)


def baixar(url, limite=None):
    pedido = urllib.request.Request(url, headers={"User-Agent": AGENTE})
    with urllib.request.urlopen(pedido, timeout=60) as resposta:
        corpo = resposta.read((limite or 20 * 1024 * 1024) + 1)
        return corpo, resposta.headers.get_content_type()


def criar_slug(texto):
    sem_acento = unicodedata.normalize("NFD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", sem_acento.lower()).strip("-")


def eh_link(texto):
    return texto.startswith(("https://", "http://"))


def ler_autores(texto):
    autores = []
    for pessoa in texto.split(";"):
        pessoa = pessoa.strip()
        if not pessoa:
            continue
        if "," in pessoa:
            sobrenome, nome = pessoa.split(",", 1)
            autores.append({"first": nome.strip(), "last": sobrenome.strip()})
        else:
            partes = pessoa.rsplit(" ", 1)
            autores.append({"first": partes[0], "last": partes[-1]})
            avisar(f'Autor sem o formato "Sobrenome, Nome": {pessoa}')
    return autores


def preparar_capa(valor, slug, titulo):
    """Devolve o caminho da capa em capas/, baixando a imagem se a planilha trouxer um link."""
    if not eh_link(valor):
        nome = Path(valor).name
        if (CAPAS / nome).is_file():
            return f"capas/{nome}"
        avisar(f'"{titulo}": o arquivo de capa {nome} não está na pasta capas.')
        return None

    existentes = sorted(CAPAS.glob(slug + ".*"))
    if existentes:
        return f"capas/{existentes[0].name}"

    try:
        corpo, tipo = baixar(valor, LIMITE_CAPA)
    except Exception as erro:
        avisar(f'"{titulo}": não consegui baixar a capa ({erro}).')
        return None
    if tipo not in EXTENSOES:
        avisar(f'"{titulo}": o link da capa não leva a uma imagem JPG, PNG ou WebP. Veio: {tipo}.')
        return None
    if len(corpo) > LIMITE_CAPA:
        avisar(f'"{titulo}": a imagem da capa passa de 5 MB.')
        return None
    destino = CAPAS / (slug + EXTENSOES[tipo])
    destino.write_bytes(corpo)
    return f"capas/{destino.name}"


def montar_livro(linha, numero):
    titulo = linha.get("Título", "").strip()
    faltando = [c for c in OBRIGATORIAS if not linha.get(c, "").strip()]
    if faltando:
        avisar(f'Linha {numero} ("{titulo or "sem título"}") ficou de fora. Falta: {", ".join(faltando)}.')
        return None

    tipo = TIPOS.get(linha["Tipo de obra"].strip())
    prateleira = PRATELEIRAS.get(linha["Prateleira"].strip())
    if not tipo or not prateleira:
        avisar(f'Linha {numero} ("{titulo}") ficou de fora. Tipo de obra ou Prateleira não reconhecidos.')
        return None

    links = {}
    for campo, coluna in (("read", "Link para ler"), ("buy", "Link para comprar"), ("video", "Link do vídeo")):
        valor = linha.get(coluna, "").strip()
        if valor and not eh_link(valor):
            avisar(f'"{titulo}": ignorei {coluna}, que não começa com http.')
            valor = ""
        links[campo] = valor

    slug = criar_slug(titulo)
    capa = preparar_capa(linha["Capa"].strip(), slug, titulo)
    if not capa:
        avisar(f'Linha {numero} ("{titulo}") ficou de fora por falta de capa.')
        return None

    lattes = [u.strip() for u in linha.get("Links do Lattes", "").split(";") if eh_link(u.strip())]
    return {
        "slug": slug,
        "title": titulo,
        "sub": linha.get("Subtítulo", "").strip(),
        "authors": ler_autores(linha["Autores"]),
        "org": linha["É organização?"].strip() == "Sim",
        "year": linha["Ano"].strip(),
        "city": linha["Cidade"].strip(),
        "pub": linha["Editora"].strip(),
        "pages": linha.get("Páginas", "").strip(),
        "isbn": linha.get("ISBN", "").strip(),
        "type": tipo,
        "shelf": prateleira,
        "cover": capa,
        **links,
        "lattes": lattes,
        "text": linha["Sinopse"].strip(),
    }


def ler_texto(caminho_csv):
    if caminho_csv:
        return Path(caminho_csv).read_text(encoding="utf-8-sig")
    url = json.loads(FONTE.read_text(encoding="utf-8")).get("csv_url", "").strip()
    if not url:
        parar("O link da planilha ainda não foi colocado em scripts/fonte.json.")
    try:
        corpo, _ = baixar(url)
    except Exception as erro:
        parar(f"Não consegui ler a planilha ({erro}).")
    return corpo.decode("utf-8-sig")


def main():
    args = argparse.ArgumentParser()
    args.add_argument("--csv")
    args.add_argument("--forcar", action="store_true")
    args = args.parse_args()

    linhas = list(csv.DictReader(io.StringIO(ler_texto(args.csv))))
    colunas = set(linhas[0]) if linhas else set()
    ausentes = (set(OBRIGATORIAS) | {"Publicar?"}) - colunas
    if ausentes:
        parar(f"A planilha não tem as colunas esperadas: {', '.join(sorted(ausentes))}.")

    CAPAS.mkdir(exist_ok=True)
    livros, vistos = [], set()
    for numero, linha in enumerate(linhas, start=2):
        if linha["Publicar?"].strip() != "Sim":
            continue
        livro = montar_livro(linha, numero)
        if not livro:
            continue
        if livro["slug"] in vistos:
            avisar(f'Linha {numero} ("{livro["title"]}") ficou de fora. Já existe um livro com esse título.')
            continue
        vistos.add(livro["slug"])
        livros.append(livro)

    if not livros:
        parar("Nenhum livro pronto para publicar. Pode ser um erro na planilha.")

    anteriores = json.loads(SAIDA.read_text(encoding="utf-8")) if SAIDA.exists() else []
    if len(anteriores) >= 4 and len(livros) < len(anteriores) / 2 and not args.forcar:
        parar(f"O número de livros caiu de {len(anteriores)} para {len(livros)}. "
              "Se for de propósito, rode a atualização com a opção de forçar.")

    SAIDA.parent.mkdir(exist_ok=True)
    SAIDA.write_text(json.dumps(livros, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(livros)} livros publicados. Avisos: {len(avisos)}.")


if __name__ == "__main__":
    main()
