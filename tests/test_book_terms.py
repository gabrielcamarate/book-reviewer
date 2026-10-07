import unittest
from revisor.book_terms import canonical_glossary, source_terms, contains_target


class BookTermsTests(unittest.TestCase):
    def test_source_terms_do_not_match_parts_of_other_words(self):
        self.assertEqual(source_terms('Emprego. Programadores. Praças. Designers.', {'ego':'ego','grama':'césped','raça':'raza','Design':'Diseño'}), [])
        self.assertEqual(source_terms('A grama cobre a praça.',{'grama':'césped'}), [('grama','césped')])

    def test_longest_phrase_overrides_embedded_terms_but_not_standalone_occurrences(self):
        glossary={'terráqueos':'terráqueos','planos terráqueos':'planos terrícolas'}
        self.assertEqual(source_terms('Os planos terráqueos.',glossary),[('planos terráqueos','planos terrícolas')])
        self.assertEqual(source_terms('Terráqueos visitam os planos terráqueos.',glossary),[('terráqueos','terráqueos'),('planos terráqueos','planos terrícolas')])

    def test_target_allows_number_inflection_and_requires_complete_words(self):
        self.assertTrue(contains_target('del quinto al duodécimo plano terrícola','planos terrícolas'))
        self.assertFalse(contains_target('Empleo. Programadores.', 'ego'))
        self.assertFalse(contains_target('Los terrícolas.', 'terráqueos'))

    def test_learned_case_variants_have_one_choice_and_explicit_glossary_wins(self):
        learned={'metrô capsulado':'metro encapsulado','Metrô Capsulado':'Metro Capsulado'}
        self.assertEqual(canonical_glossary(learned,{}),{'metrô capsulado':'metro encapsulado'})
        self.assertEqual(canonical_glossary(learned,{'Metrô Capsulado':'Metro Capsulado'}),{'Metrô Capsulado':'Metro Capsulado'})


    def test_plural_and_case_variants_still_match_after_the_quick_filter(self):
        glossary={'Terráqueos':'Terrícolas','planos':'planos','Casa das Marés':'Casa de las Mareas'}
        self.assertEqual(source_terms('O TERRÁQUEO viu um plano na casa das marés.',glossary),[('Terráqueos','Terrícolas'),('planos','planos'),('Casa das Marés','Casa de las Mareas')])
        self.assertEqual(source_terms('Nada que combine.',glossary),[])

    def test_phrase_priority_and_target_contractions_survive_number_changes(self):
        self.assertEqual(source_terms('O plano terráqueo.',{'terráqueo':'terráqueo','planos terráqueos':'planos terrícolas'}),[('planos terráqueos','planos terrícolas')])
        self.assertTrue(contains_target('la facultad del aprendizaje de la delicadeza','el aprendizaje de la delicadeza'))
        self.assertTrue(contains_target('se dirige al aprendizaje','el aprendizaje'))
