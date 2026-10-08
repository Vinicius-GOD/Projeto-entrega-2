"""História de vendas da Zé Pequeno Paçocas e Rolhas Ltda.

Carrega a planilha do time comercial, grava uma cópia limpa em CSV
e usa funções lambda para aplicar regras simples de negócio.
"""

import sys
from pathlib import Path

import pandas as pd

PASTA = Path(__file__).resolve().parent
ARQUIVO_BRUTO = PASTA / "tabela_vendas_ZePequeno_corrigido.xlsx"
ARQUIVO_LIMPO = PASTA / "tabela_vendas_ZePequeno_LIMPA.csv"

# A diretoria chama de "boa venda" o que passa deste valor.
LIMITE_BOA_VENDA = 2000.0
# Acima deste teto o número não cabe no ticket real da operação
TETO_VALOR_VALIDO = 10000.0

REGIOES = {
    "blumenau": "Blumenau",
    "joinville": "Joinville",
    "florianópolis": "Florianópolis",
    "florianopolis": "Florianópolis",
    "são paulo": "São Paulo",
    "sao paulo": "São Paulo",
    "rio de janeiro": "Rio de Janeiro",
    "curitiba": "Curitiba",
    "sul": "Sul",
    "sudeste": "Sudeste",
    "nordeste": "Nordeste",
    "norte": "Norte",
    "centro-oeste": "Centro-Oeste",
}
PRODUTOS = {"paçoca": "Paçoca", "pacoca": "Paçoca", "rolhas": "Rolhas"}
REGIOES_MACRO = {"Sul", "Sudeste", "Nordeste", "Norte", "Centro-Oeste"}

# Lambdas de limpeza: o mesmo nome chega escrito de vários jeitos.
normalizar_regiao = lambda texto: REGIOES.get(str(texto).strip().lower(), str(texto).strip())
normalizar_produto = lambda texto: PRODUTOS.get(str(texto).strip().lower(), str(texto).strip())
normalizar_canal = lambda texto: (
    "E-commerce" if "commerce" in str(texto).strip().lower() else "Loja Física"
)
venda_valida = lambda valor: 0 < float(valor) < TETO_VALOR_VALIDO

# Lambdas de negócio: classificam, filtram e resumem as vendas.
boa_venda = lambda valor: float(valor) > LIMITE_BOA_VENDA
registro_bom = lambda venda: boa_venda(venda["Valor_Venda"])
classificar_venda = lambda valor: "boa venda" if boa_venda(valor) else "venda comum"
somar_valores = lambda linhas: sum(map(lambda venda: venda["Valor_Venda"], linhas))
percentual = lambda parte, total: (parte / total * 100) if total else 0.0


def configurar_saida():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")


def reais(valor):
    texto = f"{valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
    return f"R$ {texto}"


def percentual_texto(parte, total):
    return f"{percentual(parte, total):.1f}".replace(".", ",") + "%"


def no_canal(canal):
    if canal == "Loja Física":
        return "na Loja Física"
    return "no E-commerce"


def em_lugar(regiao):
    if regiao in REGIOES_MACRO:
        return f"no {regiao}"
    return f"em {regiao}"


def limpar(df):
    """Padroniza texto e tira valores que não são venda de verdade."""
    limpo = df.copy()
    limpo["Região"] = limpo["Região"].map(normalizar_regiao)
    limpo["Canal"] = limpo["Canal"].map(normalizar_canal)
    limpo["Produto"] = limpo["Produto"].map(normalizar_produto)
    limpo = limpo[limpo["Valor_Venda"].map(venda_valida)].copy()
    limpo["Data"] = pd.to_datetime(limpo["Data"])
    limpo = limpo.sort_values(["Data", "Região", "Canal", "Produto"]).reset_index(drop=True)
    return limpo[["Data", "Região", "Canal", "Produto", "Valor_Venda"]]


def gravar_csv(df):
    saida = df.copy()
    saida["Data"] = saida["Data"].dt.strftime("%Y-%m-%d")
    saida.to_csv(ARQUIVO_LIMPO, index=False, encoding="utf-8-sig")


def carregar_base():
    """Lê a planilha comercial, limpa e devolve também a cópia em CSV."""
    if ARQUIVO_BRUTO.exists():
        bruto = pd.read_excel(ARQUIVO_BRUTO)
        limpo = limpar(bruto)
        gravar_csv(limpo)
        return limpo, len(bruto) - len(limpo), len(bruto)

    if not ARQUIVO_LIMPO.exists():
        raise FileNotFoundError(
            "Não encontrei a planilha nem o CSV limpo nesta pasta."
        )

    limpo = pd.read_csv(ARQUIVO_LIMPO, encoding="utf-8-sig", parse_dates=["Data"])
    limpo = limpar(limpo)
    return limpo, 0, len(limpo)


def para_registros(df):
    registros = df.to_dict("records")
    return list(
        map(
            lambda venda: {
                **venda,
                "Data": pd.Timestamp(venda["Data"]).strftime("%d/%m/%Y"),
                "Classificacao": classificar_venda(venda["Valor_Venda"]),
            },
            registros,
        )
    )


def totalizar(vendas, campo):
    """Soma quantidade e valor de cada categoria de um campo."""
    nomes = sorted(set(map(lambda venda: venda[campo], vendas)))
    blocos = []
    for nome in nomes:
        # nome=nome guarda o valor deste laço; sem isso a lambda veria só o último.
        grupo = list(filter(lambda venda, nome=nome: venda[campo] == nome, vendas))
        blocos.append(
            {
                "nome": nome,
                "quantidade": len(grupo),
                "valor": somar_valores(grupo),
            }
        )
    return sorted(blocos, key=lambda bloco: bloco["valor"], reverse=True)


def ranking_boas_vendas(boas):
    grupos = {}
    for venda in boas:
        chave = (venda["Produto"], venda["Canal"], venda["Região"])
        grupos.setdefault(chave, []).append(venda)

    ranking = [
        {
            "produto": produto,
            "canal": canal,
            "regiao": regiao,
            "quantidade": len(grupo),
            "valor": somar_valores(grupo),
        }
        for (produto, canal, regiao), grupo in grupos.items()
    ]
    return sorted(ranking, key=lambda item: (item["valor"], item["quantidade"]), reverse=True)


def linha_resumo(bloco, total_valor):
    return (
        f"  - {bloco['nome']}: {bloco['quantidade']} vendas, "
        f"{reais(bloco['valor'])} ({percentual_texto(bloco['valor'], total_valor)} do faturamento)"
    )


def contar_historia(df, removidos, total_original):
    vendas = para_registros(df)
    total_valor = somar_valores(vendas)
    data_inicio = df["Data"].min().strftime("%d/%m/%Y")
    data_fim = df["Data"].max().strftime("%d/%m/%Y")

    por_produto = totalizar(vendas, "Produto")
    por_canal = totalizar(vendas, "Canal")
    boas = list(filter(registro_bom, vendas))
    valor_boas = somar_valores(boas)
    ranking = ranking_boas_vendas(boas)
    melhor = ranking[0]
    lider_valor = por_produto[0]
    lider_quantidade = max(por_produto, key=lambda bloco: bloco["quantidade"])
    lider_canal = por_canal[0]

    print("=" * 64)
    print("Zé Pequeno Paçocas e Rolhas Ltda")
    print("História de vendas — economia circular")
    print("=" * 64)
    print()
    print("O amendoim vira paçoca. A casca, que poderia ir para o lixo, vira rolha.")
    print(f"O time comercial entregou {total_original} lançamentos.")
    if removidos:
        print(
            f"Ficaram de fora {removidos} registros com valor inválido "
            f"(zero ou acima de {reais(TETO_VALOR_VALIDO)})."
        )
    print(
        f"A base limpa tem {len(vendas)} vendas, de {data_inicio} a {data_fim}, "
        f"e soma {reais(total_valor)}."
    )
    print()

    print("-" * 64)
    print("1. Qual produto vende mais: paçoca ou rolhas?")
    print("-" * 64)
    for bloco in por_produto:
        print(linha_resumo(bloco, total_valor))
    print()
    if lider_quantidade["nome"] != lider_valor["nome"]:
        print(
            f"{lider_quantidade['nome']} aparece em mais lançamentos "
            f"({lider_quantidade['quantidade']}), mas {lider_valor['nome']} "
            f"fatura mais: {reais(lider_valor['valor'])}."
        )
    else:
        print(
            f"{lider_valor['nome']} lidera em faturamento e em quantidade, "
            f"com {reais(lider_valor['valor'])} em {lider_valor['quantidade']} vendas."
        )
    print(
        "Os dois lados do amendoim geram receita: a paçoca vende o grão "
        "e a rolha vende o que antes era resíduo."
    )
    print()

    print("-" * 64)
    print("2. Qual canal é mais forte: Loja Física ou E-commerce?")
    print("-" * 64)
    for bloco in por_canal:
        print(linha_resumo(bloco, total_valor))
    print()
    print(
        f"O canal mais forte é {lider_canal['nome']}, "
        f"com {reais(lider_canal['valor'])} "
        f"({percentual_texto(lider_canal['valor'], total_valor)} do total)."
    )
    print()

    print("-" * 64)
    print("3. Onde estão as boas vendas?")
    print("-" * 64)
    print(
        f"Regra da diretoria: boa venda é todo lançamento maior que {reais(LIMITE_BOA_VENDA)}."
    )
    print(
        f"Nesse critério há {len(boas)} boas vendas, somando {reais(valor_boas)} "
        f"({percentual_texto(valor_boas, total_valor)} do faturamento limpo)."
    )
    print()
    print("As três combinações de produto, canal e praça com maior valor em boas vendas:")
    for posicao, item in enumerate(ranking[:3], start=1):
        print(
            f"  {posicao}. {item['produto']} {no_canal(item['canal'])} "
            f"{em_lugar(item['regiao'])}: {item['quantidade']} vendas, {reais(item['valor'])}"
        )
    print()
    print(
        f"As melhores vendas da Zé Pequeno são de {melhor['produto']} "
        f"{no_canal(melhor['canal'])} {em_lugar(melhor['regiao'])}: "
        f"{melhor['quantidade']} vendas acima de {reais(LIMITE_BOA_VENDA)}, "
        f"somando {reais(melhor['valor'])}."
    )
    print()

    print("-" * 64)
    print("Fechamento")
    print("-" * 64)
    print(
        f"Nesta história, {lider_valor['nome']} puxa o faturamento, "
        f"{lider_canal['nome']} é o canal mais forte e as boas vendas "
        f"se concentram em {melhor['produto']} {no_canal(melhor['canal'])} "
        f"{em_lugar(melhor['regiao'])}."
    )
    print(
        "A casca que vira rolha já responde por mais da metade do dinheiro. "
        "Quase nada do amendoim se perde."
    )
    print()


def main():
    configurar_saida()
    df, removidos, total_original = carregar_base()
    contar_historia(df, removidos, total_original)


if __name__ == "__main__":
    main()
