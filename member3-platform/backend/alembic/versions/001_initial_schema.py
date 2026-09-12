"""Initial schema migration for CycloneAI platform

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-04 14:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Enable UUID extension if supported
    try:
        op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    except Exception:
        pass

    # 1. Cyclones
    op.create_table(
        'cyclones',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=True),
        sa.Column('basin', sa.String(length=50), nullable=False),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cyclones_basin'), 'cyclones', ['basin'], unique=False)
    op.create_index(op.f('ix_cyclones_is_active'), 'cyclones', ['is_active'], unique=False)

    # 2. Observations
    op.create_table(
        'observations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('cyclone_id', sa.String(length=64), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('wind_speed', sa.Float(), nullable=True),
        sa.Column('pressure', sa.Float(), nullable=True),
        sa.Column('classification', sa.String(length=50), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=False, server_default='IMD_OFFICIAL'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['cyclone_id'], ['cyclones.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_observations_cyclone_id'), 'observations', ['cyclone_id'], unique=False)
    op.create_index(op.f('ix_observations_timestamp'), 'observations', ['timestamp'], unique=False)

    # 3. Satellite Images
    op.create_table(
        'satellite_images',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('cyclone_id', sa.String(length=64), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('satellite', sa.String(length=50), nullable=False),
        sa.Column('sensor', sa.String(length=50), nullable=False),
        sa.Column('channel', sa.String(length=30), nullable=False),
        sa.Column('file_path', sa.String(length=512), nullable=False),
        sa.Column('resolution_km', sa.Float(), nullable=True),
        sa.Column('min_lat', sa.Float(), nullable=True),
        sa.Column('min_lon', sa.Float(), nullable=True),
        sa.Column('max_lat', sa.Float(), nullable=True),
        sa.Column('max_lon', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['cyclone_id'], ['cyclones.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # 4. Detection Results
    op.create_table(
        'detection_results',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('image_id', sa.String(length=64), nullable=False),
        sa.Column('detected', sa.Boolean(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=True),
        sa.Column('longitude', sa.Float(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('bbox_coordinates', sa.JSON(), nullable=True),
        sa.Column('model_version', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['image_id'], ['satellite_images.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # 5. Classification Results
    op.create_table(
        'classification_results',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('image_id', sa.String(length=64), nullable=False),
        sa.Column('cyclone_id', sa.String(length=64), nullable=True),
        sa.Column('classification', sa.String(length=50), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('estimated_wind_speed', sa.Float(), nullable=True),
        sa.Column('class_probabilities', sa.JSON(), nullable=True),
        sa.Column('explainability_file_path', sa.String(length=512), nullable=True),
        sa.Column('model_version', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['image_id'], ['satellite_images.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['cyclone_id'], ['cyclones.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # 6. Forecasts
    op.create_table(
        'forecasts',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('cyclone_id', sa.String(length=64), nullable=False),
        sa.Column('forecast_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('target_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('lead_hours', sa.Integer(), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('predicted_wind_speed', sa.Float(), nullable=True),
        sa.Column('predicted_pressure', sa.Float(), nullable=True),
        sa.Column('uncertainty_radius_km', sa.Float(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('model_version', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['cyclone_id'], ['cyclones.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_forecasts_cyclone_id'), 'forecasts', ['cyclone_id'], unique=False)
    op.create_index(op.f('ix_forecasts_target_time'), 'forecasts', ['target_time'], unique=False)

    # 7. Model Registry
    op.create_table(
        'models',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('service_name', sa.String(length=50), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('metrics', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade() -> None:
    op.drop_table('models')
    op.drop_table('forecasts')
    op.drop_table('classification_results')
    op.drop_table('detection_results')
    op.drop_table('satellite_images')
    op.drop_table('observations')
    op.drop_table('cyclones')
