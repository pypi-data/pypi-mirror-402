# Linked Data for ISDN

[ISDN (International Standard Dojin Numbering)](https://isdn.jp/) の書誌情報を Linked Data (RDFデータセット) に変換する。

## Installation

```shell
pip install isdn-ld
```

## Usage

### Convert

事前準備: [ISDN-Python](https://github.com/Babibubebon/isdn-python) で書誌情報XMLファイルをダウンロードしておく。

```shell
isdnld convert /path/to/xml_files/ /path/to/output/isdnld.nq
```

## Schema

[isdn.jp](https://isdn.jp/) が提供する書誌情報の XML Schema: <https://isdn.jp/schemas/0.1/isdn.xsd>

このXMLから少し意味的に理解を加えて設計した RDF モデルへマッピングしている。

### Vocabulary

[Schema.org](https://schema.org/) の語彙をベースとしつつ、必要に応じて以下の名前空間で独自の語彙を定義している。

- 独自語彙の名前空間: `http://metadata.moe/ns/isdn/`

### Application Profile

[DCTAP (DC Tabular Application Profiles)](https://www.dublincore.org/specifications/dctap/) でアプリケーションプロファイルを記述している。

- [tap.csv](./dctap/tap.csv)

Convert DCTAP to SHACL:

```shell
tap2shacl -c ./dctap/dctap.yml \
  -a ./dctap/about.csv \
  -ns ./dctap/namespaces.csv \
  -s ./dctap/shapes.csv \
  ./dctap/tap.csv
```

### Graph URIs

quads形式で変換すると、コンテンツのレーティングに応じてグラフURIを分ける。

- デフォルトグラフ : 一般
- `http://metadata.moe/isdn/graph/ageRestricted15` : 15禁
- `http://metadata.moe/isdn/graph/ageRestricted18` : 18禁

### Resource URI

`http://metadata.moe/isdn/res/{ISDN}`
