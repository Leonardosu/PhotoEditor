# Editor rápido de fotos

Ferramenta para colocar um texto diferente em várias de fotos.

## Como usar

1. Instale Python 3 no Windows.
2. Abra o terminal nesta pasta.
3. Execute:
   pip install pillow
4. Execute:
   python editor_fotos.py
5. Clique em "Selecionar pasta".
6. Clique na foto onde você quer que o texto fique.
7. Digite o texto.
8. Pressione Enter.
9. A foto é salva na subpasta `editadas` e a próxima aparece automaticamente.
10. A posição do texto é mantida como padrão para a próxima foto, mas você pode clicar/arrastar para mudar.

## Atalhos de texto

- `12d` -> `12打`
- `5c` -> `5盒`
- `10 d` -> `10打`
- `3 c` -> `3盒`

## Posição

- Clique diretamente na foto para posicionar o texto.
- Arraste o mouse para mover o ponto do texto.
- O ponto clicado representa o centro do texto.
- "Centralizar texto" coloca o texto no centro da foto.

## Atalhos

- Enter: salvar e próxima
- ←: foto anterior
- →: próxima foto

As fotos originais não são alteradas.