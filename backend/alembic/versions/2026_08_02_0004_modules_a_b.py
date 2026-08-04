"""create modules A (pedagogical hierarchy) and B (subscription packs)

Revision ID: 0004_modules_a_b
Revises: 0003_refresh_tokens
Create Date: 2026-08-02 23:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0004_modules_a_b'
down_revision: Union[str, None] = '0003_refresh_tokens'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # ================================================================
    # MODULE A — PÉDAGOGIQUE (tables globales, pas de school_id)
    # ================================================================

    # --- Table: competences ---
    op.create_table(
        'competences',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('nom', sa.String(200), nullable=False),
        sa.Column('matiere', sa.String(100), nullable=False),
        sa.Column('niveau_scolaire', sa.String(50), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_competences_matiere', 'competences', ['matiere'])
    op.create_index('ix_competences_niveau', 'competences', ['niveau_scolaire'])

    # --- Table: parcours ---
    op.create_table(
        'parcours',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('titre', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('matiere', sa.String(100), nullable=False),
        sa.Column('niveau_scolaire', sa.String(50), nullable=False),
        sa.Column('difficulte', sa.String(20), server_default='moyen', nullable=False),
        sa.Column('objectifs', sa.JSON()),
        sa.Column('auteur_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('est_publique', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('est_actif', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_parcours_auteur', 'parcours', ['auteur_id'])
    op.create_index('ix_parcours_matiere', 'parcours', ['matiere'])
    op.create_index('ix_parcours_niveau', 'parcours', ['niveau_scolaire'])

    # --- Table: chapitres ---
    op.create_table(
        'chapitres',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('parcours_id', sa.Integer(), sa.ForeignKey('parcours.id', ondelete='CASCADE'), nullable=False),
        sa.Column('titre', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('objectifs', sa.JSON()),
        sa.Column('ordre', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_chapitres_parcours', 'chapitres', ['parcours_id'])

    # --- Table: lecons ---
    op.create_table(
        'lecons',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('chapitre_id', sa.Integer(), sa.ForeignKey('chapitres.id', ondelete='CASCADE'), nullable=False),
        sa.Column('titre', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('duree_minutes', sa.Integer(), server_default='0', nullable=False),
        sa.Column('objectifs', sa.JSON()),
        sa.Column('ordre', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_lecons_chapitre', 'lecons', ['chapitre_id'])

    # --- Table: paragraphes ---
    op.create_table(
        'paragraphes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('lecon_id', sa.Integer(), sa.ForeignKey('lecons.id', ondelete='CASCADE'), nullable=False),
        sa.Column('parent_id', sa.Integer(), sa.ForeignKey('paragraphes.id', ondelete='CASCADE'), nullable=True),
        sa.Column('contenu', sa.Text(), nullable=False),
        sa.Column('type', sa.String(30), server_default='texte', nullable=False),
        sa.Column('ordre', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_paragraphes_lecon', 'paragraphes', ['lecon_id'])
    op.create_index('ix_paragraphes_parent', 'paragraphes', ['parent_id'])

    # --- Table: elements_pedagogiques ---
    op.create_table(
        'elements_pedagogiques',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('titre', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('lecon_id', sa.Integer(), sa.ForeignKey('lecons.id', ondelete='CASCADE'), nullable=True),
        sa.Column('paragraphe_id', sa.Integer(), sa.ForeignKey('paragraphes.id', ondelete='CASCADE'), nullable=True),
        sa.Column('matiere_id', sa.Integer(), sa.ForeignKey('matieres.id', ondelete='SET NULL'), nullable=True),
        sa.Column('niveau_etude_id', sa.Integer(), sa.ForeignKey('niveaux_etude.id', ondelete='SET NULL'), nullable=True),
        sa.Column('auteur_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('statut', sa.String(20), server_default='brouillon', nullable=False),
        sa.Column('difficulte', sa.String(20), server_default='moyen', nullable=False),
        sa.Column('metadonnees', sa.JSON()),
        sa.Column('est_global', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('est_libre', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            '(lecon_id IS NOT NULL AND paragraphe_id IS NULL) OR (lecon_id IS NULL AND paragraphe_id IS NOT NULL)',
            name='ck_element_one_parent',
        ),
    )
    op.create_index('ix_elements_type', 'elements_pedagogiques', ['type'])
    op.create_index('ix_elements_statut', 'elements_pedagogiques', ['statut'])
    op.create_index('ix_elements_auteur', 'elements_pedagogiques', ['auteur_id'])
    op.create_index('ix_elements_matiere', 'elements_pedagogiques', ['matiere_id'])
    op.create_index('ix_elements_niveau', 'elements_pedagogiques', ['niveau_etude_id'])
    op.create_index('ix_elements_lecon', 'elements_pedagogiques', ['lecon_id'])
    op.create_index('ix_elements_paragraphe', 'elements_pedagogiques', ['paragraphe_id'])

    # --- Table: elements_texte ---
    op.create_table(
        'elements_texte',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('element_id', sa.Integer(), sa.ForeignKey('elements_pedagogiques.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('corps', sa.Text(), nullable=False),
    )

    # --- Table: elements_video ---
    op.create_table(
        'elements_video',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('element_id', sa.Integer(), sa.ForeignKey('elements_pedagogiques.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('url', sa.String(500), nullable=False),
        sa.Column('duree_secondes', sa.Integer()),
        sa.Column('thumbnail_url', sa.String(500)),
    )

    # --- Table: elements_image ---
    op.create_table(
        'elements_image',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('element_id', sa.Integer(), sa.ForeignKey('elements_pedagogiques.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('url', sa.String(500), nullable=False),
        sa.Column('alt_text', sa.String(255)),
    )

    # --- Table: elements_quiz ---
    op.create_table(
        'elements_quiz',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('element_id', sa.Integer(), sa.ForeignKey('elements_pedagogiques.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('questions_json', sa.JSON(), nullable=False),
        sa.Column('score_reussite', sa.Float(), server_default='0.6', nullable=False),
    )

    # --- Table: elements_pdf ---
    op.create_table(
        'elements_pdf',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('element_id', sa.Integer(), sa.ForeignKey('elements_pedagogiques.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('url', sa.String(500), nullable=False),
        sa.Column('pages', sa.Integer()),
        sa.Column('taille_octets', sa.Integer()),
    )

    # --- Table: elements_tags_matieres (M:N junction) ---
    op.create_table(
        'elements_tags_matieres',
        sa.Column('element_id', sa.Integer(), sa.ForeignKey('elements_pedagogiques.id', ondelete='CASCADE'), nullable=False),
        sa.Column('matiere_id', sa.Integer(), sa.ForeignKey('matieres.id', ondelete='CASCADE'), nullable=False),
        sa.PrimaryKeyConstraint('element_id', 'matiere_id'),
    )

    # --- Table: elements_competences (M:N junction) ---
    op.create_table(
        'elements_competences',
        sa.Column('element_id', sa.Integer(), sa.ForeignKey('elements_pedagogiques.id', ondelete='CASCADE'), nullable=False),
        sa.Column('competence_id', sa.Integer(), sa.ForeignKey('competences.id', ondelete='CASCADE'), nullable=False),
        sa.PrimaryKeyConstraint('element_id', 'competence_id'),
    )

    # --- Table: content_workflow ---
    op.create_table(
        'content_workflow',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('element_id', sa.Integer(), sa.ForeignKey('elements_pedagogiques.id', ondelete='CASCADE'), nullable=False),
        sa.Column('ancien_statut', sa.String(20), nullable=False),
        sa.Column('nouveau_statut', sa.String(20), nullable=False),
        sa.Column('commentaires', sa.Text()),
        sa.Column('auteur_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_content_workflow_element', 'content_workflow', ['element_id'])

    # --- Table: content_promotions ---
    op.create_table(
        'content_promotions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('element_source_id', sa.Integer(), sa.ForeignKey('elements_pedagogiques.id', ondelete='CASCADE'), nullable=False),
        sa.Column('parcours_destination_id', sa.Integer(), sa.ForeignKey('parcours.id', ondelete='SET NULL'), nullable=True),
        sa.Column('snapshot_json', sa.JSON(), nullable=False),
        sa.Column('effectuee_par_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_content_promotions_element', 'content_promotions', ['element_source_id'])

    # ================================================================
    # MODULE B — COMMERCIAL (tables tenant-scoped)
    # ================================================================

    # --- Table: pack_definitions ---
    op.create_table(
        'pack_definitions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('nom', sa.String(100), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('tier', sa.String(20), nullable=False),
        sa.Column('niveau_scolaire', sa.String(50), nullable=False),
        sa.Column('matieres', sa.JSON()),
        sa.Column('prix_tnd', sa.Numeric(10, 2), nullable=False, default=0),
        sa.Column('features', sa.JSON()),
        sa.Column('est_actif', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_pack_definitions_tier', 'pack_definitions', ['tier'])
    op.create_index('ix_pack_definitions_niveau', 'pack_definitions', ['niveau_scolaire'])

    # --- Table: abonnements ---
    op.create_table(
        'abonnements',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('pack_id', sa.Integer(), sa.ForeignKey('pack_definitions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('statut', sa.String(20), server_default='actif', nullable=False),
        sa.Column('debut', sa.DateTime(), nullable=False),
        sa.Column('fin', sa.DateTime(), nullable=False),
        sa.Column('grace_fin', sa.DateTime(), nullable=True),
        sa.Column('stripe_subscription_id', sa.String(255), nullable=True),
        sa.Column('stripe_customer_id', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_abonnements_user', 'abonnements', ['user_id'])
    op.create_index('ix_abonnements_pack', 'abonnements', ['pack_id'])
    op.create_index('ix_abonnements_statut', 'abonnements', ['statut'])

    # --- Table: comptes_famille ---
    op.create_table(
        'comptes_famille',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('parent_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('max_enfants', sa.Integer(), server_default='5', nullable=False),
        sa.Column('rang_famille', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_comptes_famille_parent', 'comptes_famille', ['parent_id'])

    # --- Table: famille_enfants ---
    op.create_table(
        'famille_enfants',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('compte_famille_id', sa.Integer(), sa.ForeignKey('comptes_famille.id', ondelete='CASCADE'), nullable=False),
        sa.Column('eleve_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('rang', sa.Integer(), nullable=False),
        sa.Column('remise_pct', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('date_ajout', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_famille_enfants_compte', 'famille_enfants', ['compte_famille_id'])
    op.create_index('ix_famille_enfants_eleve', 'famille_enfants', ['eleve_id'])

    # --- Table: licences_ecole ---
    op.create_table(
        'licences_ecole',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('ecole_id', sa.Integer(), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('pack_id', sa.Integer(), sa.ForeignKey('pack_definitions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('quantite', sa.Integer(), nullable=False),
        sa.Column('quantite_disponible', sa.Integer(), nullable=False),
        sa.Column('date_achat', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_licences_ecole_ecole', 'licences_ecole', ['ecole_id'])
    op.create_index('ix_licences_ecole_pack', 'licences_ecole', ['pack_id'])

    # --- Table: licence_assignations ---
    op.create_table(
        'licence_assignations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('licence_id', sa.Integer(), sa.ForeignKey('licences_ecole.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('affecte_par_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('date_affectation', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('desaffecte_a', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_licence_assignations_licence', 'licence_assignations', ['licence_id'])
    op.create_index('ix_licence_assignations_user', 'licence_assignations', ['user_id'])


def downgrade() -> None:

    # MODULE B
    op.drop_table('licence_assignations')
    op.drop_table('licences_ecole')
    op.drop_table('famille_enfants')
    op.drop_table('comptes_famille')
    op.drop_table('abonnements')
    op.drop_table('pack_definitions')

    # MODULE A
    op.drop_table('content_promotions')
    op.drop_table('content_workflow')
    op.drop_table('elements_competences')
    op.drop_table('elements_tags_matieres')
    op.drop_table('elements_pdf')
    op.drop_table('elements_quiz')
    op.drop_table('elements_image')
    op.drop_table('elements_video')
    op.drop_table('elements_texte')
    op.drop_table('elements_pedagogiques')
    op.drop_table('paragraphes')
    op.drop_table('lecons')
    op.drop_table('chapitres')
    op.drop_table('parcours')
    op.drop_table('competences')
