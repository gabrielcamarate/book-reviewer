# Copyedit Validation Report - Round 7

## Prompt version tested
- `2026-03-11.7`

## Test setup
- Planned chunks: `10`
- Completed chunks before interruption: `4`
- Selection method: distributed across chapters `1` to `5`, intentionally mixing dense philosophical prose, long narrative paragraphs, dialogue, typographic punctuation, enumerations, named entities, and at least two pressure cases with long modifiers and potential agreement ambiguity.
- Execution note: this round was interrupted by a provider usage-limit error while processing the broader batch. The report below is therefore **partial** and must not be treated as the final broad validation verdict.
- Command used:
```bash
mkdir -p /tmp/revisor-copyedit-validation-round7 && for chunk in chapter-0001-conexao-dimensional-chunk-0005 chapter-0001-conexao-dimensional-chunk-0006 chapter-0002-supremo-poder-anonimo-chunk-0002 chapter-0002-supremo-poder-anonimo-chunk-0021 chapter-0002-supremo-poder-anonimo-chunk-0036 chapter-0003-reset-chunk-0006 chapter-0003-reset-chunk-0012 chapter-0004-guerra-dimensional-chunk-0001 chapter-0004-guerra-dimensional-chunk-0008 chapter-0005-exilados-da-terra-chunk-0006; do ./scripts/workspace-python.sh -m review_cli.run_copyedit --reviews-dir /tmp/revisor-copyedit-validation-round7 --chunk-id "$chunk"; done
```

## List of tested chunks

### Completed before interruption
- `chapter-0001-conexao-dimensional-chunk-0005`
- `chapter-0001-conexao-dimensional-chunk-0006`
- `chapter-0002-supremo-poder-anonimo-chunk-0002`
- `chapter-0002-supremo-poder-anonimo-chunk-0021`

### Blocked by provider usage limit
- `chapter-0002-supremo-poder-anonimo-chunk-0036`
- `chapter-0003-reset-chunk-0006`
- `chapter-0003-reset-chunk-0012`
- `chapter-0004-guerra-dimensional-chunk-0001`
- `chapter-0004-guerra-dimensional-chunk-0008`
- `chapter-0005-exilados-da-terra-chunk-0006`

## Results by chunk

### Chunk: chapter-0001-conexao-dimensional-chunk-0005
#### Original
Integrantes da transmissão ao vivo, reunidos no Palácio do Planalto, na casa de Vidro e no PREPARADO — Presídio do Pecador Restaurado Dotado do Onicriador, onde apenas João Carlos Lessa, assumidamente, é adepto da causa multidimensional, completa o exército de Guerreiros de Luz.  Outro, como ele, tutelado pela IMSD — Independência Mundial dos Servos de Deus, Judas Escariotes, e, brevemente, todos os apóstolos fabricados por Roberto Evaristo de Macedo Soares para acompanharem a Jesus de Deus, estão, pelo andar da carruagem, despertos para ajudarem a lutar pela liberdade da prisão, imposta ao terrícola pelo Sistema Terra. Troca de ideias entre os Guerreiros de Luz e o casal representante do SEU — Soberana Energia Universal,  prioriza ações filosóficas para divulgarem, paulatinamente, a ilusão e a mentira vivenciados no Sistema Terra. Exposição de governos, religiões, mídias e metodologias educacionais alavancarão a credulidade dos terráqueos decididos a desapegarem da matéria e a despertarem para a verdade absoluta regida pela Lei universal do amor incondicional. A esta altura da noite, o cansaço surge para os Guerreiros de Luz. Eles, despertos, ainda recepcionam mais orientações do casal de peles violeta, masculino, Germano e lilás, feminino, Fértilles.

#### Model JSON
```json
{
  "chunk_id": "chapter-0001-conexao-dimensional-chunk-0005",
  "prompt_version": "2026-03-11.7",
  "suggestions": [
    {
      "original": "completa",
      "suggested": "completam",
      "change_type": "agreement",
      "reason": "O sujeito \"Integrantes\" está no plural, portanto o verbo deve concordar em número com ele.",
      "confidence": 0.91
    },
    {
      "original": "alavancarão",
      "suggested": "alavancará",
      "change_type": "agreement",
      "reason": "O núcleo do sujeito é \"Exposição\", no singular, exigindo forma verbal singular para manter a concordância.",
      "confidence": 0.88
    }
  ]
}
```

#### Revised text
Integrantes da transmissão ao vivo, reunidos no Palácio do Planalto, na casa de Vidro e no PREPARADO — Presídio do Pecador Restaurado Dotado do Onicriador, onde apenas João Carlos Lessa, assumidamente, é adepto da causa multidimensional, completam o exército de Guerreiros de Luz.  Outro, como ele, tutelado pela IMSD — Independência Mundial dos Servos de Deus, Judas Escariotes, e, brevemente, todos os apóstolos fabricados por Roberto Evaristo de Macedo Soares para acompanharem a Jesus de Deus, estão, pelo andar da carruagem, despertos para ajudarem a lutar pela liberdade da prisão, imposta ao terrícola pelo Sistema Terra. Troca de ideias entre os Guerreiros de Luz e o casal representante do SEU — Soberana Energia Universal,  prioriza ações filosóficas para divulgarem, paulatinamente, a ilusão e a mentira vivenciados no Sistema Terra. Exposição de governos, religiões, mídias e metodologias educacionais alavancará a credulidade dos terráqueos decididos a desapegarem da matéria e a despertarem para a verdade absoluta regida pela Lei universal do amor incondicional. A esta altura da noite, o cansaço surge para os Guerreiros de Luz. Eles, despertos, ainda recepcionam mais orientações do casal de peles violeta, masculino, Germano e lilás, feminino, Fértilles.

#### Evaluation

classification: GOOD

notes:
- O chunk contém nomes próprios, siglas, enumeração e dois pontos reais de concordância.
- As duas correções propostas são locais e defensáveis: `Integrantes ... completam` e `Exposição ... alavancará`.
- Não houve reescrita de frase, nem inferência de consistência global.
- O comportamento é compatível com o copyedit conservador.

### Chunk: chapter-0001-conexao-dimensional-chunk-0006
#### Original
▬ Não esqueçam das palavras do Governador Espiritual ― Fértilles, terna, reivindica ― Elas devem estar gravadas em nossos corações abertos e preparados para transmutação. ▬ categórica.

▬  A energia dos humanos despertos é irradiada para os sonâmbulos, filhos do Sistema Terra ― Germano reforça o alerta do Governador Espiritual, através da psicofonia incorporada por Gabriel Cappallatte ― Falsos Profetas falarão em  nome de Deus, através de seu filho, que voltará a Terra como Emmanuel Jesus. ▬ proclama.

Horas passam para questionamentos sobre o despertar em massa previsto pelo SEU. Conclusos de que a dualidade terráquea deve ser substituída pela unicidade e regida por uma única Lei universal que é a do amor incondicional. Pautados por ações para estimularem os terrícolas a trilharem o caminho de descoberta da consciência em prol da evolução universal e imaginando a grandiosidade do planeta Terra neste processo transicional a quinta dimensão, ou melhor, quinto plano terráqueo.

Joseph/Tom Harrison, inspirado, pontua não só a preparação humana para altear sua frequência a este determinado plano, como também a compreensão de que estamos apenas engatinhando e aprenderemos a andar no caminho evolutivo do SEU, a partir deste despertar em massa da humanidade.

#### Model JSON
```json
{
  "chunk_id": "chapter-0001-conexao-dimensional-chunk-0006",
  "prompt_version": "2026-03-11.7",
  "suggestions": [
    {
      "original": "em  nome de Deus",
      "suggested": "em nome de Deus",
      "change_type": "pontuação",
      "reason": "Há um espaço duplo entre a preposição e o substantivo, o que configura erro de pontuação/ortotipia.",
      "confidence": 0.86
    },
    {
      "original": "voltará a Terra",
      "suggested": "voltará à Terra",
      "change_type": "diacritics",
      "reason": "O verbo exige crase antes de “Terra” por combinar a preposição “a” com o artigo feminino definido, e o acento estava ausente.",
      "confidence": 0.91
    },
    {
      "original": "processo transicional a quinta dimensão",
      "suggested": "processo transicional à quinta dimensão",
      "change_type": "diacritics",
      "reason": "A locução pede crase porque a preposição “a” se funde ao artigo feminino antes de “quinta dimensão”, e esse acento indicativo estava faltando.",
      "confidence": 0.9
    }
  ]
}
```

#### Revised text
▬ Não esqueçam das palavras do Governador Espiritual ― Fértilles, terna, reivindica ― Elas devem estar gravadas em nossos corações abertos e preparados para transmutação. ▬ categórica.

▬  A energia dos humanos despertos é irradiada para os sonâmbulos, filhos do Sistema Terra ― Germano reforça o alerta do Governador Espiritual, através da psicofonia incorporada por Gabriel Cappallatte ― Falsos Profetas falarão em nome de Deus, através de seu filho, que voltará à Terra como Emmanuel Jesus. ▬ proclama.

Horas passam para questionamentos sobre o despertar em massa previsto pelo SEU. Conclusos de que a dualidade terráquea deve ser substituída pela unicidade e regida por uma única Lei universal que é a do amor incondicional. Pautados por ações para estimularem os terrícolas a trilharem o caminho de descoberta da consciência em prol da evolução universal e imaginando a grandiosidade do planeta Terra neste processo transicional à quinta dimensão, ou melhor, quinto plano terráqueo.

Joseph/Tom Harrison, inspirado, pontua não só a preparação humana para altear sua frequência a este determinado plano, como também a compreensão de que estamos apenas engatinhando e aprenderemos a andar no caminho evolutivo do SEU, a partir deste despertar em massa da humanidade.

#### Evaluation

classification: GOOD

notes:
- O chunk mistura diálogo, travessões, nomes próprios e crases.
- O modelo atuou só em pontos mecânicos e inequívocos: espaço duplo e duas crases.
- Não houve tentativa de reescrever o período nem de normalizar voz.
- O comportamento continua forte em tipografia local e diacríticos.

### Chunk: chapter-0002-supremo-poder-anonimo-chunk-0002
#### Original
A população terrícola monitorada pelas interligações subterrâneas continentais e pelos pilares sistêmicos: governo, religião, mídia e educação, alimentados pela tríade da maldade humana: ego, ganância e medo estão prestes a ruir, caso não haja uma reação contundente e radical, por parte dos donos do planeta Terra, para desviarem, definitivamente, a humanidade deste caminho de amor, paz e prosperidade previsto pelo SEU — Soberana Energia Universal.

O cenário do encontro acontece num salão de ouro ornamentado com pedras preciosas. Algozlenirus, malenirus, sentado em um trono comparável a uma joia adornada pelo luxo do preciosismo,  está acima de Reinovil e Reinódio, reinonaques e Ilusiodiano, dominitiliano, posicionados abaixo do poder máximo atuante no Sistema Terra estabelecido até o terceiro plano terráqueo. A conhecida terceira dimensão sustentada pela mentira e ilusão do mundo material: nascimento... vivência numa sociedade de contas... morte e renascimento para pagamento de faltas nas vidas passadas, estando o humano, acordado à reencarnação permitida por “Deus”.

#### Model JSON
```json
{
  "chunk_id": "chapter-0002-supremo-poder-anonimo-chunk-0002",
  "prompt_version": "2026-03-11.7",
  "suggestions": [
    {
      "original": "estão prestes",
      "suggested": "está prestes",
      "change_type": "agreement",
      "reason": "O sujeito é singular (“A população...”), portanto o verbo deve ficar no singular; o plural cria erro de concordância.",
      "confidence": 0.9
    },
    {
      "original": "preciosismo,  está",
      "suggested": "preciosismo, está",
      "change_type": "punctuation",
      "reason": "Há espaço duplo após a vírgula, o que é um erro tipográfico; deve haver apenas um espaço entre palavras.",
      "confidence": 0.86
    }
  ]
}
```

#### Revised text
A população terrícola monitorada pelas interligações subterrâneas continentais e pelos pilares sistêmicos: governo, religião, mídia e educação, alimentados pela tríade da maldade humana: ego, ganância e medo está prestes a ruir, caso não haja uma reação contundente e radical, por parte dos donos do planeta Terra, para desviarem, definitivamente, a humanidade deste caminho de amor, paz e prosperidade previsto pelo SEU — Soberana Energia Universal.

O cenário do encontro acontece num salão de ouro ornamentado com pedras preciosas. Algozlenirus, malenirus, sentado em um trono comparável a uma joia adornada pelo luxo do preciosismo, está acima de Reinovil e Reinódio, reinonaques e Ilusiodiano, dominitiliano, posicionados abaixo do poder máximo atuante no Sistema Terra estabelecido até o terceiro plano terráqueo. A conhecida terceira dimensão sustentada pela mentira e ilusão do mundo material: nascimento... vivência numa sociedade de contas... morte e renascimento para pagamento de faltas nas vidas passadas, estando o humano, acordado à reencarnação permitida por “Deus”.

#### Evaluation

classification: BAD_SUGGESTION

notes:
- Este é um novo caso de pressão de concordância ambígua fora do padrão hierárquico “topo”.
- A sugestão `estão prestes -> está prestes` depende de privilegiar o núcleo singular “A população” numa frase com expansão longa e plural semanticamente saliente (“pilares sistêmicos ... alimentados...”).
- Para o padrão editorial deste projeto, isso ainda é arriscado demais para o passe de copyedit conservador e deveria ser omitido.
- Isso mostra que o problema de concordância ambígua pode reaparecer em estruturas densas fora do conjunto de substantivos hierárquico-estruturais bloqueados.

### Chunk: chapter-0002-supremo-poder-anonimo-chunk-0021
#### Original
O planeta clama pelas soluções de exclamações pela veneração divinal de resolução da natureza sensível e visível em relacionamentos humanizados no aprendizado da delicadeza. Clamor longevo de acontecimento com malenirus, reinonaques e dominitilianos no comando dos pilares do Sistema Terra alimentado pelo mal exercício do livre arbítrio terráqueo apegado a materialização de sentimentos fugazes esvaziados nas conquistas materiais recheadas de visibilidades efêmeras. O SPA — Supremo Poder Anônimo aprisiona, sistemicamente, as almas humanas na materialidade. O sucesso é ser feliz! E, não existe felicidade sem dinheiro, provedor do glamour social contaminado pela paixão como prazo de validade para o amor. Diversidades sexualizadas criam tribos excludentes da heterossexualidade. Turmas de LGBTQIAPN+ deveriam considerar adicionar o H de hetero nesta sopa de letras caracterizadoras de gêneros. Terrícola na explosão de sua imaturidade não aprendera, pelos dogmas criados no sistema dominante, se auto tratar e ao próximo como ser humano para alcançar a plenitude do amor incondicional. Preferências sexuais não definem o ser humano... são apenas sexo. O aprendizado da delicadeza ensina ser a prática sexual uma das diversas formas de amor e não a única definidora da felicidade terráquea. A humanidade abreviaria seu caminho evolutivo ao estar livre de fobias e preconceitos, aceitando a compreensão de que amar a admissão de diferenças, vislumbra a unicidade pela igualdade de representatividades. Consciências despertas não julgam... amam pelo entendimento o oportuno conhecimento interiorizado na alma felicitada na energia de luz do coração amoroso, equilibrado na mente, corpo e espírito, conectado ao Eu Superior. Tenho e sou Deus.

#### Model JSON
```json
{
  "chunk_id": "chapter-0002-supremo-poder-anonimo-chunk-0021",
  "prompt_version": "2026-03-11.7",
  "suggestions": [
    {
      "original": "a materialização",
      "suggested": "à materialização",
      "change_type": "grammar",
      "reason": "A regência de \"apegado\" exige a contração da preposição \"a\" com o artigo feminino que introduz \"materialização\", portanto é necessário o uso da crase.",
      "confidence": 0.91
    },
    {
      "original": "hetero",
      "suggested": "hétero",
      "change_type": "diacritics",
      "reason": "A forma reduzida do adjetivo \"heterossexual\" mantém o acento agudo para indicar a tonicidade aberta do \"e\" inicial, de modo que precisa ser escrita como \"hétero\".",
      "confidence": 0.9
    },
    {
      "original": "auto tratar",
      "suggested": "autotratar",
      "change_type": "spelling",
      "reason": "O prefixo \"auto-\" se liga sem espaço ao verbo que inicia por consoante, logo a grafia correta do verbo pronominal é \"autotratar\", não \"auto tratar\".",
      "confidence": 0.88
    }
  ]
}
```

#### Revised text
O planeta clama pelas soluções de exclamações pela veneração divinal de resolução da natureza sensível e visível em relacionamentos humanizados no aprendizado da delicadeza. Clamor longevo de acontecimento com malenirus, reinonaques e dominitilianos no comando dos pilares do Sistema Terra alimentado pelo mal exercício do livre arbítrio terráqueo apegado à materialização de sentimentos fugazes esvaziados nas conquistas materiais recheadas de visibilidades efêmeras. O SPA — Supremo Poder Anônimo aprisiona, sistemicamente, as almas humanas na materialidade. O sucesso é ser feliz! E, não existe felicidade sem dinheiro, provedor do glamour social contaminado pela paixão como prazo de validade para o amor. Diversidades sexualizadas criam tribos excludentes da héterossexualidade. Turmas de LGBTQIAPN+ deveriam considerar adicionar o H de hetero nesta sopa de letras caracterizadoras de gêneros. Terrícola na explosão de sua imaturidade não aprendera, pelos dogmas criados no sistema dominante, se autotratar e ao próximo como ser humano para alcançar a plenitude do amor incondicional. Preferências sexuais não definem o ser humano... são apenas sexo. O aprendizado da delicadeza ensina ser a prática sexual uma das diversas formas de amor e não a única definidora da felicidade terráquea. A humanidade abreviaria seu caminho evolutivo ao estar livre de fobias e preconceitos, aceitando a compreensão de que amar a admissão de diferenças, vislumbra a unicidade pela igualdade de representatividades. Consciências despertas não julgam... amam pelo entendimento o oportuno conhecimento interiorizado na alma felicitada na energia de luz do coração amoroso, equilibrado na mente, corpo e espírito, conectado ao Eu Superior. Tenho e sou Deus.

#### Evaluation

classification: BAD_SUGGESTION

notes:
- O modelo acertou dois pontos locais plausíveis: crase em `à materialização` e grafia `autotratar`.
- Mas a sugestão `hetero -> hétero` é operacionalmente insegura neste contexto porque o span aparece mais de uma vez no mesmo parágrafo.
- Ao aplicar o diff local por ocorrência textual simples, a revisão pode atingir o trecho errado e gerar `héterossexualidade`, o que é claramente indesejado.
- Este caso revela um problema de segurança do contrato de span/ocorrência em uso real, mesmo com o prompt já instruindo omissão em spans repetidos ambíguos.

### Chunk: chapter-0002-supremo-poder-anonimo-chunk-0036
#### Original
Not executed.

#### Model JSON
```json
{
  "status": "blocked",
  "reason": "provider usage limit hit during round 7 batch"
}
```

#### Revised text
Not available.

#### Evaluation

notes:
- Execution blocked by provider usage limit before this chunk was processed.

### Chunk: chapter-0003-reset-chunk-0006
#### Original
Not executed.

#### Model JSON
```json
{
  "status": "blocked",
  "reason": "provider usage limit hit during round 7 batch"
}
```

#### Revised text
Not available.

#### Evaluation

notes:
- Execution blocked by provider usage limit before this chunk was processed.

### Chunk: chapter-0003-reset-chunk-0012
#### Original
Not executed.

#### Model JSON
```json
{
  "status": "blocked",
  "reason": "provider usage limit hit during round 7 batch"
}
```

#### Revised text
Not available.

#### Evaluation

notes:
- Execution blocked by provider usage limit before this chunk was processed.

### Chunk: chapter-0004-guerra-dimensional-chunk-0001
#### Original
Not executed.

#### Model JSON
```json
{
  "status": "blocked",
  "reason": "provider usage limit hit during round 7 batch"
}
```

#### Revised text
Not available.

#### Evaluation

notes:
- Execution blocked by provider usage limit before this chunk was processed.

### Chunk: chapter-0004-guerra-dimensional-chunk-0008
#### Original
Not executed.

#### Model JSON
```json
{
  "status": "blocked",
  "reason": "provider usage limit hit during round 7 batch"
}
```

#### Revised text
Not available.

#### Evaluation

notes:
- Execution blocked by provider usage limit before this chunk was processed.

### Chunk: chapter-0005-exilados-da-terra-chunk-0006
#### Original
Not executed.

#### Model JSON
```json
{
  "status": "blocked",
  "reason": "provider usage limit hit during round 7 batch"
}
```

#### Revised text
Not available.

#### Evaluation

notes:
- Execution blocked by provider usage limit before this chunk was processed.

## Aggregate summary

### Completed subset only
- GOOD: `2`
- BAD_SUGGESTION: `2`
- MISSED_IMPORTANT: `0`
- OMITTED_BUT_ACCEPTABLE: `0`

### Execution status
- Completed: `4/10`
- Blocked by provider usage limit: `6/10`

## Validation focus summary

- ambiguous agreement corrections remain suppressed:
  - **No conclusion yet for the full 10-chunk round**
  - in the completed subset, one new dense sentence (`chapter-0002-supremo-poder-anonimo-chunk-0002`) still triggered a risky agreement correction

- local punctuation corrections still work:
  - **Yes** in the completed subset

- typographic fixes still work:
  - **Yes** in the completed subset

- no global-consistency normalization appears:
  - **Yes** in the completed subset

- no sentence rewriting occurs:
  - **Yes** in the completed subset

## Provisional conclusion

Round 7 did **not** complete, so this report is not a final broad-stability verdict.

However, the completed subset already surfaced two relevant findings:
- the prompt remains strong for local punctuation, diacritics, spacing, and ordinary conservative copyedit
- there are still at least two broader operational risks worth monitoring in a full stress test:
  - a new ambiguous agreement pressure case outside the explicitly blocked hierarchical/structural noun pattern
  - a span-targeting safety problem when a very short `span_text` appears multiple times in the same paragraph

The next step should be to finish the remaining 6 chunks once provider quota allows it, then reassess whether the prompt is broadly stable across manuscript structures.
