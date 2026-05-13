# BomScanner

Ferramenta simples para sincronizar e escanear feeds NVD (CVE) e gerar um BOM/relatório.

## Instalação

Recomenda-se criar um ambiente virtual e instalar dependências:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Uso

- Mostrar ajuda:

```bash
bomscanner help
```

- Sincronizar feeds NVD:

```bash
bomscanner sync
```

- Rodar scanner a partir de um `requirements.txt` ou `pom.xml`:

```bash
bomscanner requirements.txt
bomscanner pom.xml
```

## Estrutura

- `bomscanner/` — pacote principal com scripts de CLI e sincronização.
- `data/` — onde os feeds NVD sincronizados são armazenados.

## License

This project is licensed under the GNU General Public License v3 (GPL-3.0).
See the `COPYING` file for the full license text.
