# Zé Pequeno Paçocas e Rolhas Ltda

A Zé Pequeno usa o amendoim para fazer paçoca e reaproveita a casca para produzir rolhas. Isso é economia circular: o que seria resíduo também vira produto.

Este projeto lê a tabela de vendas, aplica regras com funções lambda e imprime um registro de vendas.

## Arquivos e para que servem

- `tabela_vendas_ZePequeno_corrigido.xlsx`: Tabela original
- `tabela_vendas_ZePequeno_LIMPA.csv`: Cópia limpa, usada na história
- `historia_vendas_lambda.py`:  Código 
- `README.md`: Este texto 

## Como executar

Na pasta do projeto, com Python, pandas e openpyxl instalados:

```bash
pip install pandas openpyxl
python historia_vendas_lambda.py
```

O script lê a planilha, regrava o CSV limpo e mostra as três análises na tela. Se a planilha não estiver na pasta, ele usa o CSV que já foi gerado.

## O que foi limpo

A planilha repete o mesmo nome de jeitos diferentes (`BLUMENAU`, `blumenau`, `ROLHAS`, `loja física`). O script padroniza região, canal e produto com lambda.

Também saem da base os valores que não são venda de verdade:

- valor igual a zero
- valor de R$ 10.000,00 ou mais (aparecem números como 99.999, 123.456 e 999.999)

Das 763 linhas originais, 29 foram removidas. A base limpa fica com 734 vendas, de 01/01/2022 a 01/04/2026. Alguns tickets muito baixos (por exemplo R$ 1,00) foram mantidos, porque a regra de corte só descarta zero e valores absurdos.

## Regras com lambda

- `normalizar_regiao`, `normalizar_produto` e `normalizar_canal` uniformizam o texto.
- `venda_valida` decide se o valor entra na base limpa.
- `boa_venda` marca venda boa quando o valor é maior que R$ 2.000,00.
- `filter`, `map` e `sorted(..., key=lambda ...)` separam, classificam e ordenam os resultados.

## As três análises

1. **Produto.** A paçoca tem mais lançamentos (368), mas as rolhas faturam mais: R$ 764.338,10, ou 51,6% do total.
2. **Canal.** A Loja Física é o canal mais forte: R$ 767.238,50, ou 51,8% do faturamento. O E-commerce fica logo atrás.
3. **Boas vendas.** Acima de R$ 2.000,00 existem 381 vendas, que concentram 62,5% do dinheiro. A melhor combinação é paçoca na Loja Física em Joinville: 43 vendas boas, somando R$ 103.851,25.

O faturamento limpo da história é R$ 1.480.567,50.
