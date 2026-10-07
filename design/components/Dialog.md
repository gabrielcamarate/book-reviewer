# Dialog

Caixa de confirmação sobre a tela, para uma decisão que afeta muitos trechos de uma vez. É a única janela do app.

**Quem usa fornece:** a pergunta como título, uma frase com a consequência e o que dá para desfazer, e os rótulos dos dois botões.

**Onde aparece:** hoje, só em "Aprovar os 12 trechos de uma vez?", no modo de aprovar à mão.

**Estrutura:** `rv-scrim` cobre a tela; dentro, `rv-dialog` com `role="dialog"`, `aria-modal="true"` e `aria-labelledby` apontando para o título. Os botões ficam em `rv-actions`.

**Regras**
- O título é a pergunta completa, com o número: "Aprovar os 12 trechos de uma vez?".
- O botão principal repete a ação com suas palavras ("Aprovar os 12"), nunca "OK" ou "Sim". O secundário leva de volta ("Voltar para conferir").
- A frase diz o que acontece e o que continua possível: "Depois, se quiser, dá para reabrir qualquer trecho."
- No celular, os botões ficam empilhados (`rv-actions--stack`), o principal em cima.
- Antes de criar outra caixa como esta, tente resolver com uma página. Formulários, listas e avisos nunca vão numa caixa.
