"""One command line over the same application service used by the interface."""
from __future__ import annotations
import argparse
import json
import shutil
from pathlib import Path

from revisor.core.import_docx import import_docx
from revisor.core.segment_manuscript import segment_extracted_manuscript
from revisor.core.review_boundary import apply_review_boundary
from revisor.core.chunking import build_review_chunks
from revisor.core.style_guide import generate_style_guide
from revisor.core.glossary import generate_glossary
from revisor.core.repository_validation import validate_repository_state
from revisor.core.consistency_report import generate_consistency_report
from revisor.core.spanish_consistency_report import generate_spanish_consistency_report
from revisor.service import ReviewService
from revisor.provider import DEFAULT_MODEL


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='Revisar, traduzir e exportar o livro localmente.')
    parser.add_argument('--root', type=Path, default=Path.cwd(), help='Raiz com o manuscrito e estado editorial.')
    parser.add_argument('--model', default=DEFAULT_MODEL, help='Modelo do Codex; padrão gpt-6.1-sol, esforço low.')
    commands = parser.add_subparsers(dest='command', required=True)
    init = commands.add_parser('import', help='Preparar um livro em uma pasta sem estado editorial.')
    init.add_argument('--input', type=Path, required=True)
    init.add_argument('--boundary', help='Trecho que inicia a revisão; antes dele é referência aprovada.')
    commands.add_parser('check', help='Validar arquivos obrigatórios.')
    commands.add_parser('state', help='Consultar o próximo trecho.')
    review = commands.add_parser('review', help='Revisar um trecho ou gerar propostas em lote.')
    review.add_argument('--chunk-id')
    review.add_argument('--batch', action='store_true')
    review.add_argument('--max-chunks', type=int)
    accept = commands.add_parser('accept', help='Aplicar a proposta do trecho atual.')
    accept.add_argument('--chunk-id', required=True)
    reject = commands.add_parser('reject', help='Recusar a proposta, registrando feedback.')
    reject.add_argument('--chunk-id', required=True)
    reject.add_argument('--reason', required=True)
    translate = commands.add_parser('translate', help='Traduzir trechos aprovados; retoma os ainda não traduzidos.')
    translate.add_argument('--max-chunks', type=int)
    export = commands.add_parser('export', help='Exportar o estado atual em Word.')
    export.add_argument('--language', choices=['pt-BR', 'es'], default='pt-BR')
    commands.add_parser('rollback', help='Reverter a última aprovação segura.')
    consistency = commands.add_parser('consistency', help='Conferir termos e padrões com regras existentes.')
    consistency.add_argument('--language', choices=['pt-BR', 'es'], default='pt-BR')
    args = parser.parse_args(argv)
    if getattr(args, 'max_chunks', None) is not None and args.max_chunks <= 0:
        parser.error('--max-chunks deve ser positivo.')
    root = args.root.resolve()
    service = ReviewService(root, model=args.model)
    try:
        if args.command == 'import':
            if (root / 'manuscript/chapters/index.json').exists():
                raise ValueError('Já existe um livro nesta pasta. Use uma pasta nova para importar outro.')
            root.mkdir(parents=True, exist_ok=True)
            source = args.input.resolve()
            if source != root / 'livro.docx':
                if (root / 'livro.docx').exists():
                    raise ValueError('livro.docx já existe; importação não sobrescreve originais.')
                shutil.copy2(source, root / 'livro.docx')
            import_docx(root / 'livro.docx', root / 'manuscript/extracted')
            segment_extracted_manuscript(root / 'manuscript/extracted', root / 'manuscript/chapters')
            if args.boundary:
                apply_review_boundary(root / 'manuscript/chapters', args.boundary)
            else:
                for file in (root / 'manuscript/chapters').glob('*.json'):
                    data = json.loads(file.read_text())
                    for paragraph in data.get('paragraphs', []):
                        paragraph['review_status'] = 'pending_review'
                    file.write_text(json.dumps(data, ensure_ascii=False, indent=2))
            build_review_chunks(chapters_dir=root / 'manuscript/chapters', output_dir=root / 'manuscript/chunks')
            (root / 'editorial').mkdir(exist_ok=True)
            if args.boundary:
                generate_style_guide(root / 'manuscript/chapters', root / 'editorial/STYLE_GUIDE.md')
                generate_glossary(root / 'manuscript/chapters', root / 'editorial/GLOSSARY.md')
            else:
                (root / 'editorial/STYLE_GUIDE.md').write_text('# Estilo\nPreservar a voz do autor; corrigir apenas erros defensáveis.\n')
                (root / 'editorial/GLOSSARY.md').write_text('# Glossário\n')
            (root / 'editorial/DECISIONS.md').write_text('# Decisões editoriais\n')
            result = validate_repository_state(root_dir=root)
        elif args.command == 'check':
            result = validate_repository_state(root_dir=root)
        elif args.command == 'state':
            result = service.state()
        elif args.command == 'consistency':
            common = dict(consolidated_dir=root / 'manuscript/consolidated',
                          glossary_path=root / 'editorial/GLOSSARY.md',
                          characters_path=root / 'editorial/CHARACTERS.md',
                          world_rules_path=root / 'editorial/WORLD_RULES.md', reports_dir=root / 'reports')
            if args.language == 'es':
                result = generate_spanish_consistency_report(translations_dir=root / 'reviews/es', **common)
            else:
                result = generate_consistency_report(**common)
        else:
            data = {k: v for k, v in vars(args).items() if k in {'chunk_id', 'reason', 'language', 'max_chunks'}}
            action = args.command
            if action == 'review':
                if args.batch:
                    action = 'review-batch'
                elif not args.chunk_id:
                    data['chunk_id'] = service.state().get('chunk', {}).get('id')
            result = service.perform(action, data)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if result.get('ok') is False or result.get('failed_count', 0) else 0
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f'Erro: {error}\n')


if __name__ == '__main__':
    raise SystemExit(main())
