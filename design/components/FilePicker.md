# FilePicker

Área para escolher o arquivo Word do livro, em dois estados: vazia (`rv-filepicker`) e com o arquivo escolhido (`rv-file`).

**Quem usa fornece:** o texto do botão ("Escolher arquivo Word"), a linha com o tipo e o tamanho aceitos e, depois da escolha, o nome do arquivo.

**Estados**
- **Vazio:** um `<button class="rv-filepicker">` grande, de borda tracejada, com o título em `primary` e a dica embaixo. Ele abre a janela de arquivos do sistema.
- **Arquivo escolhido:** `rv-file` mostra o ícone de documento, o nome em negrito, a legenda "Arquivo escolhido" e um link "Trocar arquivo".

**Regras**
- Abaixo da área, sempre a frase que tranquiliza: "Seu arquivo original não é alterado. O Revisor trabalha em uma cópia."
- Não mostre o controle de arquivo padrão do navegador.
- Arquivo recusado: explique numa frase em `rv-error` o que aconteceu e o que fazer ("Este arquivo não é um Word (.docx). Escolha outro.").
