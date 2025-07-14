"""Add personalized learning tables

Revision ID: 002_add_personalized_learning_tables
Revises: 001_initial_tables
Create Date: 2024-07-13 13:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from typing import Union, Sequence


# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "62d8e5bba881"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Add new columns to users table for personalization
    op.add_column('users', sa.Column('learning_goals', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('current_skill_level', sa.String(), nullable=True))
    op.add_column('users', sa.Column('preferred_learning_style', sa.String(), nullable=True))
    op.add_column('users', sa.Column('time_availability', sa.String(), nullable=True))
    op.add_column('users', sa.Column('career_field', sa.String(), nullable=True))
    
    # Create learning_paths table
    op.create_table('learning_paths',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('difficulty_level', sa.String(), nullable=True),
        sa.Column('estimated_duration_hours', sa.Integer(), nullable=True),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.Column('creation_date', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_learning_path_category', 'learning_paths', ['category'], unique=False)
    op.create_index('idx_learning_path_difficulty', 'learning_paths', ['difficulty_level'], unique=False)
    
    # Create learning_path_courses table
    op.create_table('learning_path_courses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('learning_path_id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('sequence_order', sa.Integer(), nullable=False),
        sa.Column('is_required', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ),
        sa.ForeignKeyConstraint(['learning_path_id'], ['learning_paths.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_learning_path_course_path_id', 'learning_path_courses', ['learning_path_id'], unique=False)
    op.create_index('idx_learning_path_course_sequence', 'learning_path_courses', ['learning_path_id', 'sequence_order'], unique=False)
    
    # Create user_learning_paths table
    op.create_table('user_learning_paths',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('learning_path_id', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('is_completed', sa.Boolean(), nullable=True),
        sa.Column('current_course_id', sa.Integer(), nullable=True),
        sa.Column('progress_percentage', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['current_course_id'], ['courses.id'], ),
        sa.ForeignKeyConstraint(['learning_path_id'], ['learning_paths.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_user_learning_path_user_id', 'user_learning_paths', ['user_id'], unique=False)
    op.create_index('idx_user_learning_path_path_id', 'user_learning_paths', ['learning_path_id'], unique=False)
    op.create_index('idx_user_learning_path_user_path', 'user_learning_paths', ['user_id', 'learning_path_id'], unique=True)
    
    # Create skill_assessments table
    op.create_table('skill_assessments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('skill_name', sa.String(), nullable=False),
        sa.Column('skill_level', sa.String(), nullable=False),
        sa.Column('assessment_date', sa.DateTime(), nullable=True),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('assessment_type', sa.String(), nullable=True),
        sa.Column('evidence_url', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_skill_assessment_user_id', 'skill_assessments', ['user_id'], unique=False)
    op.create_index('idx_skill_assessment_skill', 'skill_assessments', ['skill_name'], unique=False)
    op.create_index('idx_skill_assessment_user_skill', 'skill_assessments', ['user_id', 'skill_name'], unique=False)


def downgrade():
    # Drop indexes and tables in reverse order
    op.drop_index('idx_skill_assessment_user_skill', table_name='skill_assessments')
    op.drop_index('idx_skill_assessment_skill', table_name='skill_assessments')
    op.drop_index('idx_skill_assessment_user_id', table_name='skill_assessments')
    op.drop_table('skill_assessments')
    
    op.drop_index('idx_user_learning_path_user_path', table_name='user_learning_paths')
    op.drop_index('idx_user_learning_path_path_id', table_name='user_learning_paths')
    op.drop_index('idx_user_learning_path_user_id', table_name='user_learning_paths')
    op.drop_table('user_learning_paths')
    
    op.drop_index('idx_learning_path_course_sequence', table_name='learning_path_courses')
    op.drop_index('idx_learning_path_course_path_id', table_name='learning_path_courses')
    op.drop_table('learning_path_courses')
    
    op.drop_index('idx_learning_path_difficulty', table_name='learning_paths')
    op.drop_index('idx_learning_path_category', table_name='learning_paths')
    op.drop_table('learning_paths')
    
    # Remove columns from users table
    op.drop_column('users', 'career_field')
    op.drop_column('users', 'time_availability')
    op.drop_column('users', 'preferred_learning_style')
    op.drop_column('users', 'current_skill_level')
    op.drop_column('users', 'learning_goals')
