"""Schema-driven achievement and lesson catalog for the add-on.

This module is intentionally pure Python: no Blender imports and no filesystem
side effects. The root add-on imports these legacy dictionaries for runtime
compatibility while the catalog migration proceeds in small steps.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from typing import Any

VALID_CHECK_TYPES = {"stat", "complex"}
VALID_DIFFICULTIES = {"easy", "medium", "hard"}
VALID_REWARD_TYPES = {"tutorial", "material", "mesh", "geo_nodes", "none"}
ASSET_REWARD_TYPES = {"material", "mesh", "geo_nodes"}
ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")

ACHIEVEMENT_FIELDS = {
    "id",
    "title",
    "description",
    "goal",
    "stat_key",
    "category",
    "check_type",
    "difficulty",
    "reward_type",
    "reward_data",
    "reward_category",
    "lesson_id",
    "icon_gray",
    "icon_color",
}
COMPLEX_ACHIEVEMENT_FIELDS = ACHIEVEMENT_FIELDS | {"complex_id", "steps"}
LESSON_FIELDS = {"id", "title", "description", "category", "url", "icon"}
STEP_FIELDS = {"label", "check"}

FROZEN_ACHIEVEMENT_COUNT = 105
FROZEN_LESSON_COUNT = 9
FROZEN_CHECK_TYPES = {"stat": 40, "complex": 65}
FROZEN_CATEGORY_COUNTS = {
    "EDITING": 45,
    "MATERIALS": 17,
    "RENDERING": 17,
    "TIME": 12,
    "GEO_NODES": 14,
}
FROZEN_LESSON_CATEGORY_COUNTS = {
    "EDITING": 5,
    "MATERIALS": 1,
    "TIME": 1,
    "GEO_NODES": 1,
    "RENDERING": 1,
}
FROZEN_DIFFICULTY_COUNTS = {"easy": 10, "medium": 40, "hard": 55}
FROZEN_REWARD_TYPE_COUNTS = {
    "none": 82,
    "tutorial": 2,
    "material": 11,
    "geo_nodes": 5,
    "mesh": 5,
}
FROZEN_REWARD_CATEGORY_COUNTS = {"MESHES": 38, "SHADERS": 49, "GEO_NODES": 18}
FROZEN_STAT_KEY_COUNTS = {
    "vertices_created": 7,
    "faces_created": 6,
    "edges_created": 3,
    "materials_applied": 5,
    "renders_completed": 6,
    "time_spent": 6,
    "vertices_deleted": 3,
    "meshes_1000plus": 4,
}
FROZEN_COMPLEX_STEP_TOTAL = 85
FROZEN_COMPLEX_STEP_RANGE = (1, 4)
FROZEN_CATALOG_DIGEST = "db0e8d4bd5d596c9b0e54dac158a5c4742c33071a023914ee8287b01eea71e67"

ACH_CATEGORIES = [
    ("EDITING",    "Редактирование"),
    ("MATERIALS",  "Материалы"),
    ("GEO_NODES",  "Геометрические ноды"),
    ("TIME",       "Время в Blender"),
    ("RENDERING",  "Рендеринг"),
]

LESSON_CATEGORIES = [
    ("EDITING",    "Редактирование"),
    ("MATERIALS",  "Материалы"),
    ("GEO_NODES",  "Геометрические ноды"),
    ("TIME",       "Время в Blender"),
    ("RENDERING",  "Рендеринг"),
]

REWARD_CATEGORIES = [
    ("MESHES",      "Меши"),
    ("GEO_NODES",   "Геометрические ноды"),
    ("SHADERS",     "Шейдеры"),
    ("COMPOSITOR",  "Ноды для композитора"),
]

ACHIEVEMENTS_DEF = [
    {"id": "first_vertex", "title": "Первый шаг", "description": "Создать 1 вершину", "goal": 1, "stat_key": "vertices_created", "category": "EDITING", "check_type": "stat", "difficulty": "easy", "reward_type": "none", "reward_data": {}, "reward_category": "MESHES", "lesson_id": "lesson_vertices_basics", "icon_gray": "first_vertex_gray.png", "icon_color": "first_vertex_color.png"},
    {"id": "ten_vertices", "title": "Десятка", "description": "Создать 10 вершин", "goal": 10, "stat_key": "vertices_created", "category": "EDITING", "check_type": "stat", "difficulty": "easy", "reward_type": "none", "reward_data": {}, "reward_category": "MESHES", "lesson_id": "lesson_vertices_basics", "icon_gray": "ten_vertices_gray.png", "icon_color": "ten_vertices_color.png"},
    {"id": "first_face", "title": "Первая грань", "description": "Создать 1 грань", "goal": 1, "stat_key": "faces_created", "category": "EDITING", "check_type": "stat", "difficulty": "easy", "reward_type": "none", "reward_data": {}, "reward_category": "MESHES", "lesson_id": "lesson_faces", "icon_gray": "first_face_gray.png", "icon_color": "first_face_color.png"},
    {"id": "first_edge", "title": "Первое ребро", "description": "Создать 1 ребро", "goal": 1, "stat_key": "edges_created", "category": "EDITING", "check_type": "stat", "difficulty": "easy", "reward_type": "none", "reward_data": {}, "reward_category": "MESHES", "lesson_id": "lesson_edges", "icon_gray": "first_edge_gray.png", "icon_color": "first_edge_color.png"},
    {"id": "first_material", "title": "Художник", "description": "Применить первый материал", "goal": 1, "stat_key": "materials_applied", "category": "MATERIALS", "check_type": "stat", "difficulty": "easy", "reward_type": "none", "reward_data": {}, "reward_category": "SHADERS", "lesson_id": "lesson_materials", "icon_gray": "first_material_gray.png", "icon_color": "first_material_color.png"},
    {"id": "first_render_stat", "title": "Первый кадр", "description": "Выполнить первый рендер", "goal": 1, "stat_key": "renders_completed", "category": "RENDERING", "check_type": "stat", "difficulty": "easy", "reward_type": "none", "reward_data": {}, "reward_category": "SHADERS", "lesson_id": "lesson_render_basics", "icon_gray": "first_render_stat_gray.png", "icon_color": "first_render_stat_color.png"},
    {"id": "first_hour", "title": "Час посвящения", "description": "Провести 1 час в Blender", "goal": 3600, "stat_key": "time_spent", "category": "TIME", "check_type": "stat", "difficulty": "easy", "reward_type": "tutorial", "reward_data": {"url": "https://www.youtube.com/watch?v=time1"}, "reward_category": "SHADERS", "lesson_id": "lesson_time_management", "icon_gray": "first_hour_gray.png", "icon_color": "first_hour_color.png"},
    {"id": "hundred_vertices", "title": "Сотня", "description": "Создать 100 вершин", "goal": 100, "stat_key": "vertices_created", "category": "EDITING", "check_type": "stat", "difficulty": "easy", "reward_type": "tutorial", "reward_data": {"url": "https://www.youtube.com/watch?v=example1"}, "reward_category": "SHADERS", "lesson_id": "lesson_vertices_basics", "icon_gray": "hundred_vertices_gray.png", "icon_color": "hundred_vertices_color.png"},
    {"id": "first_deletion", "title": "Ластик", "description": "Удалить 10 вершин", "goal": 10, "stat_key": "vertices_deleted", "category": "EDITING", "check_type": "stat", "difficulty": "easy", "reward_type": "none", "reward_data": {}, "reward_category": "MESHES", "lesson_id": "lesson_edit_basics", "icon_gray": "first_deletion_gray.png", "icon_color": "first_deletion_color.png"},
    {"id": "first_dense_mesh", "title": "Плотная сетка", "description": "Создать меш с 1000+ вершинами", "goal": 1, "stat_key": "meshes_1000plus", "category": "EDITING", "check_type": "stat", "difficulty": "easy", "reward_type": "none", "reward_data": {}, "reward_category": "MESHES", "lesson_id": "lesson_modeling", "icon_gray": "first_dense_mesh_gray.png", "icon_color": "first_dense_mesh_color.png"},
    {"id": "thousand_vertices", "title": "Тысяча", "description": "Создать 1 000 вершин", "goal": 1000, "stat_key": "vertices_created", "category": "EDITING", "check_type": "stat", "difficulty": "medium", "reward_type": "material", "reward_data": {"name": "ACH_GoldPlastic", "description": "Золотистый пластик", "blend_file": "rewards/gold_plastic.blend"}, "reward_category": "SHADERS", "lesson_id": "lesson_vertices_basics", "icon_gray": "thousand_vertices_gray.png", "icon_color": "thousand_vertices_color.png"},
    {"id": "hundred_edges", "title": "Рёбра набирают силу", "description": "Создать 100 рёбер", "goal": 100, "stat_key": "edges_created", "category": "EDITING", "check_type": "stat", "difficulty": "medium", "reward_type": "none", "reward_data": {}, "reward_category": "MESHES", "lesson_id": "lesson_edges", "icon_gray": "hundred_edges_gray.png", "icon_color": "hundred_edges_color.png"},
    {"id": "hundred_faces", "title": "Многогранный мир", "description": "Создать 100 граней", "goal": 100, "stat_key": "faces_created", "category": "EDITING", "check_type": "stat", "difficulty": "medium", "reward_type": "none", "reward_data": {}, "reward_category": "MESHES", "lesson_id": "lesson_faces", "icon_gray": "hundred_faces_gray.png", "icon_color": "hundred_faces_color.png"},
    {"id": "thousand_faces", "title": "Тысяча граней", "description": "Создать 1 000 граней", "goal": 1000, "stat_key": "faces_created", "category": "EDITING", "check_type": "stat", "difficulty": "medium", "reward_type": "material", "reward_data": {"name": "ACH_StoneMat", "description": "Камень", "blend_file": "rewards/stone_mat.blend"}, "reward_category": "SHADERS", "lesson_id": "lesson_faces", "icon_gray": "thousand_faces_gray.png", "icon_color": "thousand_faces_color.png"},
    {"id": "five_dense_meshes", "title": "Коллекционер сеток", "description": "Создать 5 мешей (1000+ вершин)", "goal": 5, "stat_key": "meshes_1000plus", "category": "EDITING", "check_type": "stat", "difficulty": "medium", "reward_type": "none", "reward_data": {}, "reward_category": "MESHES", "lesson_id": "lesson_modeling", "icon_gray": "five_dense_meshes_gray.png", "icon_color": "five_dense_meshes_color.png"},
    {"id": "thousand_deletions", "title": "Разрушитель", "description": "Удалить 1 000 вершин", "goal": 1000, "stat_key": "vertices_deleted", "category": "EDITING", "check_type": "stat", "difficulty": "medium", "reward_type": "none", "reward_data": {}, "reward_category": "MESHES", "lesson_id": "lesson_edit_basics", "icon_gray": "thousand_deletions_gray.png", "icon_color": "thousand_deletions_color.png"},
    {"id": "five_materials", "title": "Палитра", "description": "Применить материалы к 5 объектам", "goal": 5, "stat_key": "materials_applied", "category": "MATERIALS", "check_type": "stat", "difficulty": "medium", "reward_type": "none", "reward_data": {}, "reward_category": "SHADERS", "lesson_id": "lesson_materials", "icon_gray": "five_materials_gray.png", "icon_color": "five_materials_color.png"},
    {"id": "ten_renders", "title": "Рендер-марафон", "description": "Выполнить 10 рендеров", "goal": 10, "stat_key": "renders_completed", "category": "RENDERING", "check_type": "stat", "difficulty": "medium", "reward_type": "none", "reward_data": {}, "reward_category": "SHADERS", "lesson_id": "lesson_render_basics", "icon_gray": "ten_renders_gray.png", "icon_color": "ten_renders_color.png"},
    {"id": "five_hours", "title": "5 часов погружения", "description": "Провести 5 часов в Blender", "goal": 18000, "stat_key": "time_spent", "category": "TIME", "check_type": "stat", "difficulty": "medium", "reward_type": "material", "reward_data": {"name": "ACH_TimeMat", "description": "Время", "blend_file": "rewards/time_mat.blend"}, "reward_category": "SHADERS", "lesson_id": "lesson_time_management", "icon_gray": "five_hours_gray.png", "icon_color": "five_hours_color.png"},
    {"id": "ten_hours", "title": "10 часов мастерства", "description": "Провести 10 часов в Blender", "goal": 36000, "stat_key": "time_spent", "category": "TIME", "check_type": "stat", "difficulty": "medium", "reward_type": "none", "reward_data": {}, "reward_category": "SHADERS", "lesson_id": "lesson_time_management", "icon_gray": "ten_hours_gray.png", "icon_color": "ten_hours_color.png"},
    {"id": "fifty_renders", "title": "Рендер-конвейер", "description": "Выполнить 50 рендеров", "goal": 50, "stat_key": "renders_completed", "category": "RENDERING", "check_type": "stat", "difficulty": "medium", "reward_type": "none", "reward_data": {}, "reward_category": "SHADERS", "lesson_id": "lesson_render_basics", "icon_gray": "fifty_renders_gray.png", "icon_color": "fifty_renders_color.png"},
    {"id": "twenty_materials", "title": "Коллекция материалов", "description": "Применить 20 материалов", "goal": 20, "stat_key": "materials_applied", "category": "MATERIALS", "check_type": "stat", "difficulty": "medium", "reward_type": "material", "reward_data": {"name": "ACH_RainbowMat", "description": "Радуга", "blend_file": "rewards/rainbow_mat.blend"}, "reward_category": "SHADERS", "lesson_id": "lesson_materials", "icon_gray": "twenty_materials_gray.png", "icon_color": "twenty_materials_color.png"},
    {"id": "twenty_hours", "title": "Двадцать часов", "description": "Провести 20 часов в Blender", "goal": 72000, "stat_key": "time_spent", "category": "TIME", "check_type": "stat", "difficulty": "medium", "reward_type": "none", "reward_data": {}, "reward_category": "SHADERS", "lesson_id": "lesson_time_management", "icon_gray": "twenty_hours_gray.png", "icon_color": "twenty_hours_color.png"},
    {"id": "hundred_renders", "title": "Сто кадров", "description": "Выполнить 100 рендеров", "goal": 100, "stat_key": "renders_completed", "category": "RENDERING", "check_type": "stat", "difficulty": "medium", "reward_type": "material", "reward_data": {"name": "ACH_RenderGlow", "description": "Свечение рендера", "blend_file": "rewards/render_glow.blend"}, "reward_category": "SHADERS", "lesson_id": "lesson_render_basics", "icon_gray": "hundred_renders_gray.png", "icon_color": "hundred_renders_color.png"},
    {"id": "ten_thousand_deletions", "title": "Великое удаление", "description": "Удалить 10 000 вершин", "goal": 10000, "stat_key": "vertices_deleted", "category": "EDITING", "check_type": "stat", "difficulty": "medium", "reward_type": "none", "reward_data": {}, "reward_category": "MESHES", "lesson_id": None, "icon_gray": "ten_thousand_deletions_gray.png", "icon_color": "ten_thousand_deletions_color.png"},
    {"id": "five_modifier_stack", "title": "Башня модификаторов", "description": "5+ модификаторов на объекте", "goal": 1, "stat_key": "_complex", "category": "EDITING", "check_type": "complex", "complex_id": "five_modifier_stack", "difficulty": "medium", "reward_type": "none", "reward_data": {}, "reward_category": "MESHES", "lesson_id": None, "steps": [{"label": "Меш в сцене", "check": "has_mesh"}, {"label": "5+ модификаторов", "check": "five_modifier_stack"}], "icon_gray": "five_modifier_stack_gray.png", "icon_color": "five_modifier_stack_color.png"},
    {"id": "mirror_subdivision", "title": "Симметричный субдив", "description": "Mirror + Subdivision Surface", "goal": 1, "stat_key": "_complex", "category": "EDITING", "check_type": "complex", "complex_id": "mirror_subdivision", "difficulty": "medium", "reward_type": "none", "reward_data": {}, "reward_category": "MESHES", "lesson_id": "lesson_modeling", "steps": [{"label": "Mirror", "check": "has_mirror"}, {"label": "Subdivision", "check": "has_subsurf"}], "icon_gray": "mirror_subdivision_gray.png", "icon_color": "mirror_subdivision_color.png"},
    {"id": "boolean_master", "title": "Булев мастер", "description": "Boolean для вычитания/объединения", "goal": 1, "stat_key": "_complex", "category": "EDITING", "check_type": "complex", "complex_id": "boolean_master", "difficulty": "medium", "reward_type": "none", "reward_data": {}, "reward_category": "MESHES", "lesson_id": None, "steps": [{"label": "Boolean модификатор", "check": "has_boolean"}], "icon_gray": "boolean_master_gray.png", "icon_color": "boolean_master_color.png"},
    {"id": "solidify_bevel_combo", "title": "Объём и фаска", "description": "Solidify + Bevel на объекте", "goal": 1, "stat_key": "_complex", "category": "EDITING", "check_type": "complex", "complex_id": "solidify_bevel_combo", "difficulty": "medium", "reward_type": "none", "reward_data": {}, "reward_category": "MESHES", "lesson_id": None, "steps": [{"label": "Solidify", "check": "has_solidify"}, {"label": "Bevel", "check": "has_bevel"}], "icon_gray": "solidify_bevel_combo_gray.png", "icon_color": "solidify_bevel_combo_color.png"},
    {"id": "screw_modifier", "title": "Токарь", "description": "Модификатор Screw", "goal": 1, "stat_key": "_complex", "category": "EDITING", "check_type": "complex", "complex_id": "screw_modifier", "difficulty": "medium", "reward_type": "none", "reward_data": {}, "reward_category": "MESHES", "lesson_id": None, "steps": [{"label": "Screw модификатор", "check": "has_screw"}], "icon_gray": "screw_modifier_gray.png", "icon_color": "screw_modifier_color.png"},
    {"id": "collection_organizer", "title": "Порядок в сцене", "description": "5+ коллекций с объектами", "goal": 1, "stat_key": "_complex", "category": "EDITING", "check_type": "complex", "complex_id": "collection_organizer", "difficulty": "medium", "reward_type": "none", "reward_data": {}, "reward_category": "MESHES", "lesson_id": None, "steps": [{"label": "5+ коллекций", "check": "has_5_collections"}], "icon_gray": "collection_organizer_gray.png", "icon_color": "collection_organizer_color.png"},
    {"id": "custom_origin", "title": "Точка опоры", "description": "Переместить Origin объекта", "goal": 1, "stat_key": "_complex", "category": "EDITING", "check_type": "complex", "complex_id": "custom_origin", "difficulty": "medium", "reward_type": "none", "reward_data": {}, "reward_category": "MESHES", "lesson_id": None, "steps": [{"label": "Origin перемещён", "check": "custom_origin_set"}], "icon_gray": "custom_origin_gray.png", "icon_color": "custom_origin_color.png"},
    {"id": "linked_duplicate", "title": "Клон-армия", "description": "20+ связанных дубликатов (Alt+D)", "goal": 1, "stat_key": "_complex", "category": "EDITING", "check_type": "complex", "complex_id": "linked_duplicate", "difficulty": "medium", "reward_type": "none", "reward_data": {}, "reward_category": "MESHES", "lesson_id": None, "steps": [{"label": "20+ linked duplicates", "check": "has_20_linked"}], "icon_gray": "linked_duplicate_gray.png", "icon_color": "linked_duplicate_color.png"},
    {"id": "ten_lights_scene", "title": "Световое шоу", "description": "10+ источников света в сцене", "goal": 1, "stat_key": "_complex", "category": "RENDERING", "check_type": "complex", "complex_id": "ten_lights_scene", "difficulty": "medium", "reward_type": "none", "reward_data": {}, "reward_category": "SHADERS", "lesson_id": "lesson_render_basics", "steps": [{"label": "10+ источников света", "check": "has_10_lights"}], "icon_gray": "ten_lights_scene_gray.png", "icon_color": "ten_lights_scene_color.png"},
    {"id": "three_light_setup", "title": "Трёхточечный свет", "description": "3 типа источников света", "goal": 1, "stat_key": "_complex", "category": "RENDERING", "check_type": "complex", "complex_id": "three_light_setup", "difficulty": "medium", "reward_type": "none", "reward_data": {}, "reward_category": "SHADERS", "lesson_id": "lesson_render_basics", "steps": [{"label": "3+ разных типа света", "check": "has_3_light_types"}], "icon_gray": "three_light_setup_gray.png", "icon_color": "three_light_setup_color.png"},
    {"id": "hdri_lighting", "title": "Студийный свет", "description": "HDRI как окружающее освещение", "goal": 1, "stat_key": "_complex", "category": "RENDERING", "check_type": "complex", "complex_id": "hdri_lighting", "difficulty": "medium", "reward_type": "none", "reward_data": {}, "reward_category": "SHADERS", "lesson_id": "lesson_render_basics", "steps": [{"label": "HDRI Environment Texture", "check": "has_hdri"}], "icon_gray": "hdri_lighting_gray.png", "icon_color": "hdri_lighting_color.png"},
    {"id": "depth_of_field", "title": "Боке мастер", "description": "Depth of Field с объектом фокуса", "goal": 1, "stat_key": "_complex", "category": "RENDERING", "check_type": "complex", "complex_id": "depth_of_field", "difficulty": "medium", "reward_type": "none", "reward_data": {}, "reward_category": "SHADERS", "lesson_id": "lesson_render_basics", "steps": [{"label": "DoF включён + фокус", "check": "has_dof"}], "icon_gray": "depth_of_field_gray.png", "icon_color": "depth_of_field_color.png"},
    {"id": "motion_blur_render", "title": "Размытие движения", "description": "Рендер с Motion Blur", "goal": 1, "stat_key": "_complex", "category": "RENDERING", "check_type": "complex", "complex_id": "motion_blur_render", "difficulty": "medium", "reward_type": "none", "reward_data": {}, "reward_category": "SHADERS", "lesson_id": "lesson_render_basics", "steps": [{"label": "Motion Blur включён", "check": "has_motion_blur"}], "icon_gray": "motion_blur_render_gray.png", "icon_color": "motion_blur_render_color.png"},
    {"id": "denoiser_render", "title": "Чистый кадр", "description": "Рендер с деноизером", "goal": 1, "stat_key": "_complex", "category": "RENDERING", "check_type": "complex", "complex_id": "denoiser_render", "difficulty": "medium", "reward_type": "none", "reward_data": {}, "reward_category": "SHADERS", "lesson_id": "lesson_render_basics", "steps": [{"label": "Деноизер включён", "check": "has_denoiser"}], "icon_gray": "denoiser_render_gray.png", "icon_color": "denoiser_render_color.png"},
    {"id": "texture_paint", "title": "Живопись по модели", "description": "Texture Paint на меше", "goal": 1, "stat_key": "_complex", "category": "MATERIALS", "check_type": "complex", "complex_id": "texture_paint", "difficulty": "medium", "reward_type": "none", "reward_data": {}, "reward_category": "SHADERS", "lesson_id": "lesson_materials", "steps": [{"label": "Texture Paint активирован", "check": "has_texture_paint"}], "icon_gray": "texture_paint_gray.png", "icon_color": "texture_paint_color.png"},
    {"id": "uv_unwrap_material", "title": "Картограф", "description": "UV-развёртка + текстурная карта", "goal": 1, "stat_key": "_complex", "category": "MATERIALS", "check_type": "complex", "complex_id": "uv_unwrap_material", "difficulty": "medium", "reward_type": "none", "reward_data": {}, "reward_category": "SHADERS", "lesson_id": "lesson_materials", "steps": [{"label": "UV Map", "check": "has_uv"}, {"label": "Image Texture в материале", "check": "has_image_texture"}], "icon_gray": "uv_unwrap_material_gray.png", "icon_color": "uv_unwrap_material_color.png"},
    {"id": "emission_material", "title": "Светящийся объект", "description": "Материал с Emission", "goal": 1, "stat_key": "_complex", "category": "MATERIALS", "check_type": "complex", "complex_id": "emission_material", "difficulty": "medium", "reward_type": "none", "reward_data": {}, "reward_category": "SHADERS", "lesson_id": "lesson_materials", "steps": [{"label": "Emission нод", "check": "has_emission"}], "icon_gray": "emission_material_gray.png", "icon_color": "emission_material_color.png"},
    {"id": "glass_ior", "title": "Стеклодув", "description": "Glass BSDF с IOR 1.45-1.52", "goal": 1, "stat_key": "_complex", "category": "MATERIALS", "check_type": "complex", "complex_id": "glass_ior", "difficulty": "medium", "reward_type": "none", "reward_data": {}, "reward_category": "SHADERS", "lesson_id": "lesson_materials", "steps": [{"label": "Glass BSDF с IOR", "check": "has_glass_ior"}], "icon_gray": "glass_ior_gray.png", "icon_color": "glass_ior_color.png"},
    {"id": "mix_shader", "title": "Смешанный шейдер", "description": "Mix Shader для двух BSDF", "goal": 1, "stat_key": "_complex", "category": "MATERIALS", "check_type": "complex", "complex_id": "mix_shader", "difficulty": "medium", "reward_type": "none", "reward_data": {}, "reward_category": "SHADERS", "lesson_id": "lesson_materials", "steps": [{"label": "Mix Shader", "check": "has_mix_shader"}], "icon_gray": "mix_shader_gray.png", "icon_color": "mix_shader_color.png"},
    {"id": "first_geonode", "title": "Нодовый дебют", "description": "Первый Geometry Nodes модификатор", "goal": 1, "stat_key": "_complex", "category": "GEO_NODES", "check_type": "complex", "complex_id": "first_geonode", "difficulty": "medium", "reward_type": "none", "reward_data": {}, "reward_category": "GEO_NODES", "lesson_id": "lesson_geo_nodes_intro", "steps": [{"label": "GN модификатор", "check": "has_geonodes_mod"}], "icon_gray": "first_geonode_gray.png", "icon_color": "first_geonode_color.png"},
    {"id": "geonode_instance", "title": "Размножитель", "description": "Instance on Points в GN", "goal": 1, "stat_key": "_complex", "category": "GEO_NODES", "check_type": "complex", "complex_id": "geonode_instance", "difficulty": "medium", "reward_type": "none", "reward_data": {}, "reward_category": "GEO_NODES", "lesson_id": "lesson_geo_nodes_intro", "steps": [{"label": "Instance on Points", "check": "has_gn_instance"}], "icon_gray": "geonode_instance_gray.png", "icon_color": "geonode_instance_color.png"},
    {"id": "geonode_scatter", "title": "Художник природы", "description": "Distribute Points on Faces", "goal": 1, "stat_key": "_complex", "category": "GEO_NODES", "check_type": "complex", "complex_id": "geonode_scatter", "difficulty": "medium", "reward_type": "none", "reward_data": {}, "reward_category": "GEO_NODES", "lesson_id": "lesson_geo_nodes_intro", "steps": [{"label": "Distribute Points on Faces", "check": "has_gn_scatter"}], "icon_gray": "geonode_scatter_gray.png", "icon_color": "geonode_scatter_color.png"},
    {"id": "night_session", "title": "Ночной трудяга", "description": "Сессия с 22:00 до 02:00", "goal": 1, "stat_key": "_complex", "category": "TIME", "check_type": "complex", "complex_id": "night_session", "difficulty": "medium", "reward_type": "none", "reward_data": {}, "reward_category": "SHADERS", "lesson_id": None, "steps": [{"label": "Ночная сессия", "check": "is_night_session"}], "icon_gray": "night_session_gray.png", "icon_color": "night_session_color.png"},
    {"id": "daily_streak_7", "title": "Неделя преданности", "description": "Blender 7 дней подряд", "goal": 1, "stat_key": "_complex", "category": "TIME", "check_type": "complex", "complex_id": "daily_streak_7", "difficulty": "medium", "reward_type": "none", "reward_data": {}, "reward_category": "SHADERS", "lesson_id": None, "steps": [{"label": "7 дней подряд", "check": "has_7_day_streak"}], "icon_gray": "daily_streak_7_gray.png", "icon_color": "daily_streak_7_color.png"},
    {"id": "ten_thousand_vertices", "title": "Десять тысяч", "description": "Создать 10 000 вершин", "goal": 10000, "stat_key": "vertices_created", "category": "EDITING", "check_type": "stat", "difficulty": "hard", "reward_type": "material", "reward_data": {"name": "ACH_ChromeMetal", "description": "Хром", "blend_file": "rewards/chrome_metal.blend"}, "reward_category": "SHADERS", "lesson_id": None, "icon_gray": "ten_thousand_vertices_gray.png", "icon_color": "ten_thousand_vertices_color.png"},
    {"id": "ten_thousand_edges", "title": "Рёбра без счёта", "description": "Создать 10 000 рёбер", "goal": 10000, "stat_key": "edges_created", "category": "EDITING", "check_type": "stat", "difficulty": "hard", "reward_type": "none", "reward_data": {}, "reward_category": "MESHES", "lesson_id": None, "icon_gray": "ten_thousand_edges_gray.png", "icon_color": "ten_thousand_edges_color.png"},
    {"id": "ten_thousand_faces", "title": "Полигональный бог", "description": "Создать 10 000 граней", "goal": 10000, "stat_key": "faces_created", "category": "EDITING", "check_type": "stat", "difficulty": "hard", "reward_type": "material", "reward_data": {"name": "ACH_WireMat", "description": "Проволока", "blend_file": "rewards/wire_mat.blend"}, "reward_category": "SHADERS", "lesson_id": None, "icon_gray": "ten_thousand_faces_gray.png", "icon_color": "ten_thousand_faces_color.png"},
    {"id": "ten_dense_meshes", "title": "Фабрика сеток", "description": "10 мешей (1000+ вершин)", "goal": 10, "stat_key": "meshes_1000plus", "category": "EDITING", "check_type": "stat", "difficulty": "hard", "reward_type": "geo_nodes", "reward_data": {"name": "ACH_ArrayPattern", "description": "Массив", "blend_file": "rewards/array_pattern.blend"}, "reward_category": "GEO_NODES", "lesson_id": None, "icon_gray": "ten_dense_meshes_gray.png", "icon_color": "ten_dense_meshes_color.png"},
    {"id": "hundred_thousand_vertices", "title": "Сто тысяч", "description": "Создать 100 000 вершин", "goal": 100000, "stat_key": "vertices_created", "category": "EDITING", "check_type": "stat", "difficulty": "hard", "reward_type": "geo_nodes", "reward_data": {"name": "ACH_ScatterGrass", "description": "Разброс травы", "blend_file": "rewards/scatter_grass.blend"}, "reward_category": "GEO_NODES", "lesson_id": None, "icon_gray": "hundred_thousand_vertices_gray.png", "icon_color": "hundred_thousand_vertices_color.png"},
    {"id": "million_vertices", "title": "Миллион вершин", "description": "Создать 1 000 000 вершин", "goal": 1000000, "stat_key": "vertices_created", "category": "EDITING", "check_type": "stat", "difficulty": "hard", "reward_type": "mesh", "reward_data": {"name": "ACH_CrownMesh", "description": "Корона", "blend_file": "rewards/crown_mesh.blend"}, "reward_category": "MESHES", "lesson_id": None, "icon_gray": "million_vertices_gray.png", "icon_color": "million_vertices_color.png"},
    {"id": "fifty_dense_meshes", "title": "Архитектор высокого поли", "description": "50 мешей (1000+ вершин)", "goal": 50, "stat_key": "meshes_1000plus", "category": "EDITING", "check_type": "stat", "difficulty": "hard", "reward_type": "mesh", "reward_data": {"name": "ACH_EraseSphere", "description": "Сфера-призрак", "blend_file": "rewards/erase_sphere.blend"}, "reward_category": "MESHES", "lesson_id": None, "icon_gray": "fifty_dense_meshes_gray.png", "icon_color": "fifty_dense_meshes_color.png"},
    {"id": "hundred_thousand_faces", "title": "Стена полигонов", "description": "Создать 100 000 граней", "goal": 100000, "stat_key": "faces_created", "category": "EDITING", "check_type": "stat", "difficulty": "hard", "reward_type": "none", "reward_data": {}, "reward_category": "MESHES", "lesson_id": None, "icon_gray": "hundred_thousand_faces_gray.png", "icon_color": "hundred_thousand_faces_color.png"},
    {"id": "million_faces", "title": "Полигональная вселенная", "description": "Создать 1 000 000 граней", "goal": 1000000, "stat_key": "faces_created", "category": "EDITING", "check_type": "stat", "difficulty": "hard", "reward_type": "none", "reward_data": {}, "reward_category": "MESHES", "lesson_id": None, "icon_gray": "million_faces_gray.png", "icon_color": "million_faces_color.png"},
    {"id": "fifty_hours", "title": "Пятьдесят часов", "description": "Провести 50 часов в Blender", "goal": 180000, "stat_key": "time_spent", "category": "TIME", "check_type": "stat", "difficulty": "hard", "reward_type": "mesh", "reward_data": {"name": "ACH_ClockMesh", "description": "Часы", "blend_file": "rewards/clock_mesh.blend"}, "reward_category": "MESHES", "lesson_id": None, "icon_gray": "fifty_hours_gray.png", "icon_color": "fifty_hours_color.png"},
    {"id": "hundred_hours", "title": "Сотня часов", "description": "Провести 100 часов в Blender", "goal": 360000, "stat_key": "time_spent", "category": "TIME", "check_type": "stat", "difficulty": "hard", "reward_type": "geo_nodes", "reward_data": {"name": "ACH_TimeVortex", "description": "Временная воронка", "blend_file": "rewards/time_vortex.blend"}, "reward_category": "GEO_NODES", "lesson_id": None, "icon_gray": "hundred_hours_gray.png", "icon_color": "hundred_hours_color.png"},
    {"id": "five_hundred_renders", "title": "Рендер-фабрика", "description": "500 рендеров", "goal": 500, "stat_key": "renders_completed", "category": "RENDERING", "check_type": "stat", "difficulty": "hard", "reward_type": "none", "reward_data": {}, "reward_category": "SHADERS", "lesson_id": None, "icon_gray": "five_hundred_renders_gray.png", "icon_color": "five_hundred_renders_color.png"},
    {"id": "thousand_renders", "title": "Тысяча кадров", "description": "1 000 рендеров", "goal": 1000, "stat_key": "renders_completed", "category": "RENDERING", "check_type": "stat", "difficulty": "hard", "reward_type": "none", "reward_data": {}, "reward_category": "SHADERS", "lesson_id": None, "icon_gray": "thousand_renders_gray.png", "icon_color": "thousand_renders_color.png"},
    {"id": "hundred_materials", "title": "Материальный мастер", "description": "100 материалов", "goal": 100, "stat_key": "materials_applied", "category": "MATERIALS", "check_type": "stat", "difficulty": "hard", "reward_type": "material", "reward_data": {"name": "ACH_LifeMat", "description": "Жизнь", "blend_file": "rewards/life_mat.blend"}, "reward_category": "SHADERS", "lesson_id": None, "icon_gray": "hundred_materials_gray.png", "icon_color": "hundred_materials_color.png"},
    {"id": "fifty_materials", "title": "Материальное богатство", "description": "50 материалов", "goal": 50, "stat_key": "materials_applied", "category": "MATERIALS", "check_type": "stat", "difficulty": "hard", "reward_type": "none", "reward_data": {}, "reward_category": "SHADERS", "lesson_id": None, "icon_gray": "fifty_materials_gray.png", "icon_color": "fifty_materials_color.png"},
    {"id": "array_circle", "title": "Круговой массив", "description": "Array + Empty для кругового расположения", "goal": 1, "stat_key": "_complex", "category": "EDITING", "check_type": "complex", "complex_id": "array_circle", "difficulty": "hard", "reward_type": "none", "reward_data": {}, "reward_category": "MESHES", "lesson_id": None, "steps": [{"label": "Array + Empty", "check": "has_array_with_empty"}], "icon_gray": "array_circle_gray.png", "icon_color": "array_circle_color.png"},
    {"id": "ten_modifier_stack", "title": "Башня до небес", "description": "10+ модификаторов на объекте", "goal": 1, "stat_key": "_complex", "category": "EDITING", "check_type": "complex", "complex_id": "ten_modifier_stack", "difficulty": "hard", "reward_type": "none", "reward_data": {}, "reward_category": "MESHES", "lesson_id": None, "steps": [{"label": "10+ модификаторов", "check": "ten_modifier_stack"}], "icon_gray": "ten_modifier_stack_gray.png", "icon_color": "ten_modifier_stack_color.png"},
    {"id": "shrinkwrap_use", "title": "Обёртка", "description": "Shrinkwrap с target", "goal": 1, "stat_key": "_complex", "category": "EDITING", "check_type": "complex", "complex_id": "shrinkwrap_use", "difficulty": "hard", "reward_type": "none", "reward_data": {}, "reward_category": "MESHES", "lesson_id": None, "steps": [{"label": "Shrinkwrap + target", "check": "has_shrinkwrap"}], "icon_gray": "shrinkwrap_use_gray.png", "icon_color": "shrinkwrap_use_color.png"},
    {"id": "armature_modifier", "title": "Анатом", "description": "Armature модификатор + арматура", "goal": 1, "stat_key": "_complex", "category": "EDITING", "check_type": "complex", "complex_id": "armature_modifier", "difficulty": "hard", "reward_type": "none", "reward_data": {}, "reward_category": "MESHES", "lesson_id": None, "steps": [{"label": "Armature модификатор", "check": "has_armature"}], "icon_gray": "armature_modifier_gray.png", "icon_color": "armature_modifier_color.png"},
    {"id": "curve_deform", "title": "Изгиб пространства", "description": "Curve деформация", "goal": 1, "stat_key": "_complex", "category": "EDITING", "check_type": "complex", "complex_id": "curve_deform", "difficulty": "hard", "reward_type": "none", "reward_data": {}, "reward_category": "MESHES", "lesson_id": None, "steps": [{"label": "Curve модификатор", "check": "has_curve_mod"}], "icon_gray": "curve_deform_gray.png", "icon_color": "curve_deform_color.png"},
    {"id": "skin_modifier", "title": "Кожа", "description": "Модификатор Skin", "goal": 1, "stat_key": "_complex", "category": "EDITING", "check_type": "complex", "complex_id": "skin_modifier", "difficulty": "hard", "reward_type": "none", "reward_data": {}, "reward_category": "MESHES", "lesson_id": None, "steps": [{"label": "Skin модификатор", "check": "has_skin"}], "icon_gray": "skin_modifier_gray.png", "icon_color": "skin_modifier_color.png"},
    {"id": "weighted_normals", "title": "Мягкий свет", "description": "Weighted Normal модификатор", "goal": 1, "stat_key": "_complex", "category": "EDITING", "check_type": "complex", "complex_id": "weighted_normals", "difficulty": "hard", "reward_type": "none", "reward_data": {}, "reward_category": "MESHES", "lesson_id": None, "steps": [{"label": "Weighted Normal", "check": "has_weighted_normal"}], "icon_gray": "weighted_normals_gray.png", "icon_color": "weighted_normals_color.png"},
    {"id": "shape_key_animation", "title": "Форма меняется", "description": "Shape Keys с анимацией", "goal": 1, "stat_key": "_complex", "category": "EDITING", "check_type": "complex", "complex_id": "shape_key_animation", "difficulty": "hard", "reward_type": "none", "reward_data": {}, "reward_category": "MESHES", "lesson_id": None, "steps": [{"label": "2+ Shape Keys", "check": "has_shape_keys"}, {"label": "Анимация", "check": "has_shape_key_anim"}], "icon_gray": "shape_key_animation_gray.png", "icon_color": "shape_key_animation_color.png"},
    {"id": "multiresolution_sculpt", "title": "Скульптор", "description": "Multiresolution + скульптинг", "goal": 1, "stat_key": "_complex", "category": "EDITING", "check_type": "complex", "complex_id": "multiresolution_sculpt", "difficulty": "hard", "reward_type": "none", "reward_data": {}, "reward_category": "MESHES", "lesson_id": None, "steps": [{"label": "Multiresolution", "check": "has_multires"}], "icon_gray": "multiresolution_sculpt_gray.png", "icon_color": "multiresolution_sculpt_color.png"},
    {"id": "retopology_work", "title": "Топологический хирург", "description": "Ретопология с Snap to Face", "goal": 1, "stat_key": "_complex", "category": "EDITING", "check_type": "complex", "complex_id": "retopology_work", "difficulty": "hard", "reward_type": "none", "reward_data": {}, "reward_category": "MESHES", "lesson_id": None, "steps": [{"label": "Snap to Face активен", "check": "has_snap_face"}], "icon_gray": "retopology_work_gray.png", "icon_color": "retopology_work_color.png"},
    {"id": "particle_system", "title": "Повелитель частиц", "description": "Система частиц + ветер", "goal": 1, "stat_key": "_complex", "category": "EDITING", "check_type": "complex", "complex_id": "particle_system", "difficulty": "hard", "reward_type": "none", "reward_data": {}, "reward_category": "MESHES", "lesson_id": None, "steps": [{"label": "Система частиц", "check": "has_particles"}], "icon_gray": "particle_system_gray.png", "icon_color": "particle_system_color.png"},
    {"id": "cycles_caustics", "title": "Каустика", "description": "Cycles каустика + преломление", "goal": 1, "stat_key": "_complex", "category": "RENDERING", "check_type": "complex", "complex_id": "cycles_caustics", "difficulty": "hard", "reward_type": "none", "reward_data": {}, "reward_category": "SHADERS", "lesson_id": None, "steps": [{"label": "Cycles каустика", "check": "has_caustics"}], "icon_gray": "cycles_caustics_gray.png", "icon_color": "cycles_caustics_color.png"},
    {"id": "volumetric_render", "title": "Объёмный туман", "description": "Volume Scatter в сцене", "goal": 1, "stat_key": "_complex", "category": "RENDERING", "check_type": "complex", "complex_id": "volumetric_render", "difficulty": "hard", "reward_type": "none", "reward_data": {}, "reward_category": "SHADERS", "lesson_id": None, "steps": [{"label": "Volume шейдер", "check": "has_volume"}], "icon_gray": "volumetric_render_gray.png", "icon_color": "volumetric_render_color.png"},
    {"id": "compositing_node_render", "title": "Режиссёр пост-продакшна", "description": "Compositor ноды", "goal": 1, "stat_key": "_complex", "category": "RENDERING", "check_type": "complex", "complex_id": "compositing_node_render", "difficulty": "hard", "reward_type": "none", "reward_data": {}, "reward_category": "SHADERS", "lesson_id": None, "steps": [{"label": "Compositor ноды", "check": "has_compositor"}], "icon_gray": "compositing_node_render_gray.png", "icon_color": "compositing_node_render_color.png"},
    {"id": "render_passes", "title": "Мультиканальный рендер", "description": "5+ рендер-пассов", "goal": 1, "stat_key": "_complex", "category": "RENDERING", "check_type": "complex", "complex_id": "render_passes", "difficulty": "hard", "reward_type": "none", "reward_data": {}, "reward_category": "SHADERS", "lesson_id": None, "steps": [{"label": "5+ пассов включено", "check": "has_5_passes"}], "icon_gray": "render_passes_gray.png", "icon_color": "render_passes_color.png"},
    {"id": "principled_bsdf_full", "title": "Физик", "description": "Все основные входы Principled BSDF", "goal": 1, "stat_key": "_complex", "category": "MATERIALS", "check_type": "complex", "complex_id": "principled_bsdf_full", "difficulty": "hard", "reward_type": "material", "reward_data": {"name": "ACH_EraseMat", "description": "Прозрачный", "blend_file": "rewards/erase_mat.blend"}, "reward_category": "SHADERS", "lesson_id": "lesson_materials", "steps": [{"label": "Base Color подключён", "check": "has_base_color"}, {"label": "Normal подключён", "check": "has_normal_input"}], "icon_gray": "principled_bsdf_full_gray.png", "icon_color": "principled_bsdf_full_color.png"},
    {"id": "normal_map_material", "title": "Иллюзия рельефа", "description": "Normal Map в материале", "goal": 1, "stat_key": "_complex", "category": "MATERIALS", "check_type": "complex", "complex_id": "normal_map_material", "difficulty": "hard", "reward_type": "none", "reward_data": {}, "reward_category": "SHADERS", "lesson_id": "lesson_materials", "steps": [{"label": "Normal Map нод", "check": "has_normal_map"}], "icon_gray": "normal_map_material_gray.png", "icon_color": "normal_map_material_color.png"},
    {"id": "subsurface_skin", "title": "Сквозь кожу", "description": "Subsurface Scattering", "goal": 1, "stat_key": "_complex", "category": "MATERIALS", "check_type": "complex", "complex_id": "subsurface_skin", "difficulty": "hard", "reward_type": "none", "reward_data": {}, "reward_category": "SHADERS", "lesson_id": "lesson_materials", "steps": [{"label": "Subsurface > 0", "check": "has_subsurface"}], "icon_gray": "subsurface_skin_gray.png", "icon_color": "subsurface_skin_color.png"},
    {"id": "procedural_texture", "title": "Без текстур", "description": "Процедурный материал без изображений", "goal": 1, "stat_key": "_complex", "category": "MATERIALS", "check_type": "complex", "complex_id": "procedural_texture", "difficulty": "hard", "reward_type": "none", "reward_data": {}, "reward_category": "SHADERS", "lesson_id": "lesson_materials", "steps": [{"label": "Процедурные ноды", "check": "has_procedural"}, {"label": "Нет Image Texture", "check": "no_image_texture"}], "icon_gray": "procedural_texture_gray.png", "icon_color": "procedural_texture_color.png"},
    {"id": "vertex_color_material", "title": "Вершинная краска", "description": "Vertex Color в материале", "goal": 1, "stat_key": "_complex", "category": "MATERIALS", "check_type": "complex", "complex_id": "vertex_color_material", "difficulty": "hard", "reward_type": "none", "reward_data": {}, "reward_category": "SHADERS", "lesson_id": None, "steps": [{"label": "Color Attribute нод", "check": "has_vertex_color"}], "icon_gray": "vertex_color_material_gray.png", "icon_color": "vertex_color_material_color.png"},
    {"id": "displacement_material", "title": "Настоящий рельеф", "description": "Displacement в Material Output", "goal": 1, "stat_key": "_complex", "category": "MATERIALS", "check_type": "complex", "complex_id": "displacement_material", "difficulty": "hard", "reward_type": "none", "reward_data": {}, "reward_category": "SHADERS", "lesson_id": None, "steps": [{"label": "Displacement подключён", "check": "has_displacement"}], "icon_gray": "displacement_material_gray.png", "icon_color": "displacement_material_color.png"},
    {"id": "geonode_attribute", "title": "Атрибут-мастер", "description": "Пользовательский атрибут в GN", "goal": 1, "stat_key": "_complex", "category": "GEO_NODES", "check_type": "complex", "complex_id": "geonode_attribute", "difficulty": "hard", "reward_type": "none", "reward_data": {}, "reward_category": "GEO_NODES", "lesson_id": None, "steps": [{"label": "Store/Named Attribute", "check": "has_gn_attribute"}], "icon_gray": "geonode_attribute_gray.png", "icon_color": "geonode_attribute_color.png"},
    {"id": "geonode_curve_to_mesh", "title": "Трубопрокладчик", "description": "Curve to Mesh в GN", "goal": 1, "stat_key": "_complex", "category": "GEO_NODES", "check_type": "complex", "complex_id": "geonode_curve_to_mesh", "difficulty": "hard", "reward_type": "none", "reward_data": {}, "reward_category": "GEO_NODES", "lesson_id": None, "steps": [{"label": "Curve to Mesh нод", "check": "has_gn_curve_to_mesh"}], "icon_gray": "geonode_curve_to_mesh_gray.png", "icon_color": "geonode_curve_to_mesh_color.png"},
    {"id": "geonode_noise_deform", "title": "Органический шум", "description": "Noise + Set Position в GN", "goal": 1, "stat_key": "_complex", "category": "GEO_NODES", "check_type": "complex", "complex_id": "geonode_noise_deform", "difficulty": "hard", "reward_type": "none", "reward_data": {}, "reward_category": "GEO_NODES", "lesson_id": None, "steps": [{"label": "Noise Texture", "check": "has_gn_noise"}, {"label": "Set Position", "check": "has_gn_set_position"}], "icon_gray": "geonode_noise_deform_gray.png", "icon_color": "geonode_noise_deform_color.png"},
    {"id": "geonode_group_input", "title": "Параметрический объект", "description": "Group Input с параметрами", "goal": 1, "stat_key": "_complex", "category": "GEO_NODES", "check_type": "complex", "complex_id": "geonode_group_input", "difficulty": "hard", "reward_type": "none", "reward_data": {}, "reward_category": "GEO_NODES", "lesson_id": None, "steps": [{"label": "Group Input с параметрами", "check": "has_gn_group_input"}], "icon_gray": "geonode_group_input_gray.png", "icon_color": "geonode_group_input_color.png"},
    {"id": "geonode_boolean_node", "title": "Нодовый булеан", "description": "Mesh Boolean в GN", "goal": 1, "stat_key": "_complex", "category": "GEO_NODES", "check_type": "complex", "complex_id": "geonode_boolean_node", "difficulty": "hard", "reward_type": "none", "reward_data": {}, "reward_category": "GEO_NODES", "lesson_id": None, "steps": [{"label": "Mesh Boolean нод", "check": "has_gn_boolean"}], "icon_gray": "geonode_boolean_node_gray.png", "icon_color": "geonode_boolean_node_color.png"},
    {"id": "geonode_realize_instances", "title": "Реализация", "description": "Realize Instances в GN", "goal": 1, "stat_key": "_complex", "category": "GEO_NODES", "check_type": "complex", "complex_id": "geonode_realize_instances", "difficulty": "hard", "reward_type": "none", "reward_data": {}, "reward_category": "GEO_NODES", "lesson_id": None, "steps": [{"label": "Realize Instances", "check": "has_gn_realize"}], "icon_gray": "geonode_realize_instances_gray.png", "icon_color": "geonode_realize_instances_color.png"},
    {"id": "geonode_simulation", "title": "Симулятор", "description": "Simulation Zone в GN", "goal": 1, "stat_key": "_complex", "category": "GEO_NODES", "check_type": "complex", "complex_id": "geonode_simulation", "difficulty": "hard", "reward_type": "none", "reward_data": {}, "reward_category": "GEO_NODES", "lesson_id": None, "steps": [{"label": "Simulation Zone", "check": "has_gn_simulation"}], "icon_gray": "geonode_simulation_gray.png", "icon_color": "geonode_simulation_color.png"},
    {"id": "weekend_marathon", "title": "Выходной с Blender", "description": "6+ часов в выходной", "goal": 1, "stat_key": "_complex", "category": "TIME", "check_type": "complex", "complex_id": "weekend_marathon", "difficulty": "hard", "reward_type": "none", "reward_data": {}, "reward_category": "SHADERS", "lesson_id": None, "steps": [{"label": "6+ часов в выходной", "check": "is_weekend_marathon"}], "icon_gray": "weekend_marathon_gray.png", "icon_color": "weekend_marathon_color.png"},
    {"id": "daily_streak_30", "title": "Месяц преданности", "description": "Blender 30 дней подряд", "goal": 1, "stat_key": "_complex", "category": "TIME", "check_type": "complex", "complex_id": "daily_streak_30", "difficulty": "hard", "reward_type": "none", "reward_data": {}, "reward_category": "SHADERS", "lesson_id": None, "steps": [{"label": "30 дней подряд", "check": "has_30_day_streak"}], "icon_gray": "daily_streak_30_gray.png", "icon_color": "daily_streak_30_color.png"},
    {"id": "speed_modeler", "title": "Скоростное моделирование", "description": "500+ вершин за 5 минут", "goal": 1, "stat_key": "_complex", "category": "TIME", "check_type": "complex", "complex_id": "speed_modeler", "difficulty": "hard", "reward_type": "none", "reward_data": {}, "reward_category": "SHADERS", "lesson_id": None, "steps": [{"label": "500+ вершин за 5 мин", "check": "is_speed_modeler"}], "icon_gray": "speed_modeler_gray.png", "icon_color": "speed_modeler_color.png"},
    {"id": "early_bird", "title": "Ранняя пташка", "description": "Сессия с 05:00 до 08:00", "goal": 1, "stat_key": "_complex", "category": "TIME", "check_type": "complex", "complex_id": "early_bird", "difficulty": "hard", "reward_type": "none", "reward_data": {}, "reward_category": "SHADERS", "lesson_id": None, "steps": [{"label": "Утренняя сессия", "check": "is_early_bird"}], "icon_gray": "early_bird_gray.png", "icon_color": "early_bird_color.png"},
    {"id": "blender_legend", "title": "Легенда Blender", "description": "Разблокировать 50 достижений", "goal": 1, "stat_key": "_complex", "category": "EDITING", "check_type": "complex", "complex_id": "blender_legend", "difficulty": "hard", "reward_type": "mesh", "reward_data": {"name": "ACH_StarMesh", "description": "Звезда", "blend_file": "rewards/star_mesh.blend"}, "reward_category": "MESHES", "lesson_id": None, "steps": [{"label": "50+ достижений", "check": "has_50_unlocked"}], "icon_gray": "blender_legend_gray.png", "icon_color": "blender_legend_color.png"},
    {"id": "smooth_cube", "title": "Гладкий куб", "description": "Меш + Subdivision Surface", "goal": 1, "stat_key": "_complex", "category": "EDITING", "check_type": "complex", "complex_id": "smooth_cube", "difficulty": "medium", "reward_type": "material", "reward_data": {"name": "ACH_SmoothMat", "description": "Гладкий пластик", "blend_file": "rewards/smooth_mat.blend"}, "reward_category": "SHADERS", "lesson_id": "lesson_modeling", "steps": [{"label": "Добавить меш", "check": "has_mesh"}, {"label": "Subdivision Surface", "check": "has_subsurf"}], "icon_gray": "smooth_cube_gray.png", "icon_color": "smooth_cube_color.png"},
    {"id": "sphere_from_cube", "title": "Сфера из куба", "description": "Subdivision + Smooth by Angle", "goal": 1, "stat_key": "_complex", "category": "EDITING", "check_type": "complex", "complex_id": "sphere_from_cube", "difficulty": "hard", "reward_type": "mesh", "reward_data": {"name": "ACH_PerfectSphere", "description": "Идеальная сфера", "blend_file": "rewards/perfect_sphere.blend"}, "reward_category": "MESHES", "lesson_id": "lesson_modeling", "steps": [{"label": "Добавить меш", "check": "has_mesh"}, {"label": "Subdivision Surface", "check": "has_subsurf"}, {"label": "Smooth by Angle", "check": "has_smooth"}], "icon_gray": "sphere_from_cube_gray.png", "icon_color": "sphere_from_cube_color.png"},
    {"id": "first_render", "title": "Первый рендер", "description": "Рендер с объектом, материалом и светом", "goal": 1, "stat_key": "_complex", "category": "RENDERING", "check_type": "complex", "complex_id": "first_render", "difficulty": "hard", "reward_type": "material", "reward_data": {"name": "ACH_RenderGlowComplex", "description": "Свечение", "blend_file": "rewards/render_glow.blend"}, "reward_category": "SHADERS", "lesson_id": "lesson_render_basics", "steps": [{"label": "Меш в сцене", "check": "has_mesh"}, {"label": "Материал на меше", "check": "has_material_on_mesh"}, {"label": "Источник света", "check": "has_light"}, {"label": "Запустить рендер", "check": "render_done"}], "icon_gray": "first_render_gray.png", "icon_color": "first_render_color.png"},
    {"id": "architect", "title": "Архитектор", "description": "3 объекта + уникальные материалы + Array", "goal": 1, "stat_key": "_complex", "category": "MATERIALS", "check_type": "complex", "complex_id": "architect", "difficulty": "hard", "reward_type": "geo_nodes", "reward_data": {"name": "ACH_ArchGeo", "description": "Архитектурная нода", "blend_file": "rewards/arch_geo.blend"}, "reward_category": "GEO_NODES", "lesson_id": None, "steps": [{"label": "Коллекция создана", "check": "has_collection"}, {"label": "3+ меша", "check": "has_3_meshes"}, {"label": "Уникальные материалы", "check": "has_unique_mats"}, {"label": "Array", "check": "has_array"}], "icon_gray": "architect_gray.png", "icon_color": "architect_color.png"},
    {"id": "procedural_master", "title": "Процедурный мастер", "description": "GN с 3+ нодами + материал", "goal": 1, "stat_key": "_complex", "category": "GEO_NODES", "check_type": "complex", "complex_id": "procedural_master", "difficulty": "hard", "reward_type": "geo_nodes", "reward_data": {"name": "ACH_ProceduralGeo", "description": "Процедурная нода", "blend_file": "rewards/procedural_geo.blend"}, "reward_category": "GEO_NODES", "lesson_id": None, "steps": [{"label": "Меш с материалом", "check": "has_mesh_with_mat"}, {"label": "GN модификатор", "check": "has_geonodes_mod"}, {"label": "3+ ноды", "check": "has_3_nodes"}, {"label": "Связи", "check": "has_links"}], "icon_gray": "procedural_master_gray.png", "icon_color": "procedural_master_color.png"},
    {"id": "geonode_convex_hull", "title": "Выпуклая оболочка", "description": "Convex Hull в GN", "goal": 1, "stat_key": "_complex", "category": "GEO_NODES", "check_type": "complex", "complex_id": "geonode_convex_hull", "difficulty": "hard", "reward_type": "none", "reward_data": {}, "reward_category": "GEO_NODES", "lesson_id": None, "steps": [{"label": "Convex Hull нод", "check": "has_gn_convex_hull"}], "icon_gray": "geonode_convex_hull_gray.png", "icon_color": "geonode_convex_hull_color.png"},
    {"id": "geonode_field_math", "title": "Полевая математика", "description": "Field-ноды + математика в GN", "goal": 1, "stat_key": "_complex", "category": "GEO_NODES", "check_type": "complex", "complex_id": "geonode_field_math", "difficulty": "hard", "reward_type": "none", "reward_data": {}, "reward_category": "GEO_NODES", "lesson_id": None, "steps": [{"label": "Field at/Evaluate at Index", "check": "has_gn_field_math"}], "icon_gray": "geonode_field_math_gray.png", "icon_color": "geonode_field_math_color.png"},
    {"id": "geonode_domain_switch", "title": "Домен-мастер", "description": "Перенос атрибутов между доменами в GN", "goal": 1, "stat_key": "_complex", "category": "GEO_NODES", "check_type": "complex", "complex_id": "geonode_domain_switch", "difficulty": "hard", "reward_type": "none", "reward_data": {}, "reward_category": "GEO_NODES", "lesson_id": None, "steps": [{"label": "Sample Index/Transfer Attribute", "check": "has_gn_domain_switch"}], "icon_gray": "geonode_domain_switch_gray.png", "icon_color": "geonode_domain_switch_color.png"},
]

LESSONS_DEF = [
    {"id": "lesson_vertices_basics", "title": "Основы вершин",
     "description": "Создание, удаление, перемещение",
     "category": "EDITING",
     "url": "https://www.youtube.com/watch?v=lesson_verts", "icon": "lesson_verts.png"},
    {"id": "lesson_edit_basics", "title": "Основы редактирования",
     "description": "Edit Mode: базовые операции",
     "category": "EDITING",
     "url": "https://www.youtube.com/watch?v=lesson_edit", "icon": "lesson_edit.png"},
    {"id": "lesson_edges", "title": "Работа с рёбрами",
     "description": "Loop Cut, Bevel, Knife",
     "category": "EDITING",
     "url": "https://www.youtube.com/watch?v=lesson_edges", "icon": "lesson_edges.png"},
    {"id": "lesson_faces", "title": "Работа с гранями",
     "description": "Extrude, Inset, Fill",
     "category": "EDITING",
     "url": "https://www.youtube.com/watch?v=lesson_faces", "icon": "lesson_faces.png"},
    {"id": "lesson_modeling", "title": "Моделирование",
     "description": "От простого к сложному",
     "category": "EDITING",
     "url": "https://www.youtube.com/watch?v=lesson_modeling", "icon": "lesson_modeling.png"},
    {"id": "lesson_materials", "title": "Материалы и шейдинг",
     "description": "Principled BSDF, ноды",
     "category": "MATERIALS",
     "url": "https://www.youtube.com/watch?v=lesson_materials", "icon": "lesson_materials.png"},
    {"id": "lesson_time_management", "title": "Организация работы",
     "description": "Горячие клавиши, workflow",
     "category": "TIME",
     "url": "https://www.youtube.com/watch?v=lesson_time", "icon": "lesson_time.png"},
    {"id": "lesson_geo_nodes_intro", "title": "Введение в Geometry Nodes",
     "description": "Основные ноды, первый граф",
     "category": "GEO_NODES",
     "url": "https://www.youtube.com/watch?v=lesson_geonodes", "icon": "lesson_geonodes.png"},
    {"id": "lesson_render_basics", "title": "Основы рендеринга",
     "description": "Eevee, Cycles, настройки",
     "category": "RENDERING",
     "url": "https://www.youtube.com/watch?v=lesson_render", "icon": "lesson_render.png"},
]

def _as_sorted_dict(counter: Counter[str]) -> dict[str, int]:
    return dict(sorted(counter.items()))


def catalog_payload() -> dict[str, list[dict[str, Any]]]:
    return {"achievements": ACHIEVEMENTS_DEF, "lessons": LESSONS_DEF}


def catalog_digest() -> str:
    payload = json.dumps(catalog_payload(), ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def catalog_counts() -> dict[str, Any]:
    stat_step_counts = [
        len(item.get("steps", []))
        for item in ACHIEVEMENTS_DEF
        if item.get("check_type") == "complex"
    ]
    return {
        "achievement_count": len(ACHIEVEMENTS_DEF),
        "lesson_count": len(LESSONS_DEF),
        "check_types": _as_sorted_dict(Counter(item.get("check_type") for item in ACHIEVEMENTS_DEF)),
        "achievement_categories": _as_sorted_dict(Counter(item.get("category") for item in ACHIEVEMENTS_DEF)),
        "lesson_categories": _as_sorted_dict(Counter(item.get("category") for item in LESSONS_DEF)),
        "difficulty_counts": _as_sorted_dict(Counter(item.get("difficulty") for item in ACHIEVEMENTS_DEF)),
        "reward_types": _as_sorted_dict(Counter(item.get("reward_type") for item in ACHIEVEMENTS_DEF)),
        "reward_categories": _as_sorted_dict(Counter(item.get("reward_category") for item in ACHIEVEMENTS_DEF)),
        "stat_keys": _as_sorted_dict(
            Counter(
                item.get("stat_key")
                for item in ACHIEVEMENTS_DEF
                if item.get("check_type") == "stat"
            )
        ),
        "complex_step_total": sum(stat_step_counts),
        "complex_step_range": [min(stat_step_counts), max(stat_step_counts)] if stat_step_counts else [0, 0],
        "first_achievement_id": ACHIEVEMENTS_DEF[0]["id"] if ACHIEVEMENTS_DEF else "",
        "last_achievement_id": ACHIEVEMENTS_DEF[-1]["id"] if ACHIEVEMENTS_DEF else "",
        "first_lesson_id": LESSONS_DEF[0]["id"] if LESSONS_DEF else "",
        "last_lesson_id": LESSONS_DEF[-1]["id"] if LESSONS_DEF else "",
    }


def _append_count_error(errors: list[str], label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        errors.append(f"{label}: expected {expected!r}, got {actual!r}")


def validate_catalog() -> list[str]:
    errors: list[str] = []
    ach_category_ids = {key for key, _label in ACH_CATEGORIES}
    lesson_category_ids = {key for key, _label in LESSON_CATEGORIES}
    reward_category_ids = {key for key, _label in REWARD_CATEGORIES}
    lesson_ids = [item.get("id") for item in LESSONS_DEF]
    lesson_id_set = set(lesson_ids)
    achievement_ids = [item.get("id") for item in ACHIEVEMENTS_DEF]
    complex_ids_all = [
        item.get("complex_id") for item in ACHIEVEMENTS_DEF if item.get("check_type") == "complex"
    ]
    valid_stat_keys = set(FROZEN_STAT_KEY_COUNTS) | {"_complex"}

    if len(achievement_ids) != len(set(achievement_ids)):
        errors.append("achievement ids are not unique")
    if len(lesson_ids) != len(set(lesson_ids)):
        errors.append("lesson ids are not unique")
    if len(complex_ids_all) != len(set(complex_ids_all)):
        errors.append("complex ids are not unique")

    for item in ACHIEVEMENTS_DEF:
        aid = item.get("id", "<missing>")
        expected_fields = (
            COMPLEX_ACHIEVEMENT_FIELDS
            if item.get("check_type") == "complex"
            else ACHIEVEMENT_FIELDS
        )
        missing = expected_fields - set(item)
        extra = set(item) - expected_fields
        if missing:
            errors.append(f"{aid}: missing {sorted(missing)[0]}")
        if extra:
            errors.append(f"{aid}: extra {sorted(extra)[0]}")
        if not isinstance(item.get("id"), str) or not ID_PATTERN.match(item["id"]):
            errors.append(f"{aid}: id")
        for text_key in ["title", "description", "icon_gray", "icon_color"]:
            if not isinstance(item.get(text_key), str) or not item[text_key]:
                errors.append(f"{aid}: {text_key}")
        if not isinstance(item.get("goal"), int) or item["goal"] <= 0:
            errors.append(f"{aid}: goal")
        if item.get("category") not in ach_category_ids:
            errors.append(f"{aid}: category")
        if item.get("check_type") not in VALID_CHECK_TYPES:
            errors.append(f"{aid}: check_type")
        if item.get("difficulty") not in VALID_DIFFICULTIES:
            errors.append(f"{aid}: difficulty")
        if item.get("reward_type") not in VALID_REWARD_TYPES:
            errors.append(f"{aid}: reward_type")
        if item.get("reward_category") not in reward_category_ids:
            errors.append(f"{aid}: reward_category")
        if item.get("stat_key") not in valid_stat_keys:
            errors.append(f"{aid}: stat_key")
        lesson_id = item.get("lesson_id")
        if lesson_id is not None and lesson_id not in lesson_id_set:
            errors.append(f"{aid}: lesson_id")
        reward_type = item.get("reward_type")
        reward_data = item.get("reward_data")
        if reward_type == "tutorial":
            if not isinstance(reward_data, dict) or not reward_data.get("url"):
                errors.append(f"{aid}: tutorial url")
        elif reward_type in ASSET_REWARD_TYPES:
            for key in ["name", "description", "blend_file"]:
                if not isinstance(reward_data, dict) or not reward_data.get(key):
                    errors.append(f"{aid}: reward {key}")
        elif reward_type == "none" and reward_data != {}:
            errors.append(f"{aid}: none reward_data")
        if item.get("check_type") == "complex":
            if item.get("stat_key") != "_complex":
                errors.append(f"{aid}: complex stat_key")
            complex_id = item.get("complex_id")
            if not isinstance(complex_id, str) or not complex_id:
                errors.append(f"{aid}: complex_id")
            steps = item.get("steps")
            if not isinstance(steps, list) or not steps:
                errors.append(f"{aid}: steps")
            else:
                for step in steps:
                    if not isinstance(step, dict) or not step.get("label") or not step.get("check"):
                        errors.append(f"{aid}: step")
                    elif set(step) != STEP_FIELDS:
                        errors.append(f"{aid}: step fields")
        elif "complex_id" in item or "steps" in item:
            errors.append(f"{aid}: stat complex fields")

    for item in LESSONS_DEF:
        lid = item.get("id", "<missing>")
        missing = LESSON_FIELDS - set(item)
        extra = set(item) - LESSON_FIELDS
        if missing:
            errors.append(f"{lid}: missing {sorted(missing)[0]}")
        if extra:
            errors.append(f"{lid}: extra {sorted(extra)[0]}")
        if not isinstance(item.get("id"), str) or not ID_PATTERN.match(item["id"]):
            errors.append(f"{lid}: lesson id")
        if item.get("category") not in lesson_category_ids:
            errors.append(f"{lid}: lesson category")
        for text_key in ["title", "description", "url", "icon"]:
            if not isinstance(item.get(text_key), str) or not item[text_key]:
                errors.append(f"{lid}: {text_key}")

    counts = catalog_counts()
    _append_count_error(errors, "achievement_count", counts["achievement_count"], FROZEN_ACHIEVEMENT_COUNT)
    _append_count_error(errors, "lesson_count", counts["lesson_count"], FROZEN_LESSON_COUNT)
    _append_count_error(errors, "check_types", counts["check_types"], FROZEN_CHECK_TYPES)
    _append_count_error(errors, "achievement_categories", counts["achievement_categories"], FROZEN_CATEGORY_COUNTS)
    _append_count_error(errors, "lesson_categories", counts["lesson_categories"], FROZEN_LESSON_CATEGORY_COUNTS)
    _append_count_error(errors, "difficulty_counts", counts["difficulty_counts"], FROZEN_DIFFICULTY_COUNTS)
    _append_count_error(errors, "reward_types", counts["reward_types"], FROZEN_REWARD_TYPE_COUNTS)
    _append_count_error(errors, "reward_categories", counts["reward_categories"], FROZEN_REWARD_CATEGORY_COUNTS)
    _append_count_error(errors, "stat_keys", counts["stat_keys"], FROZEN_STAT_KEY_COUNTS)
    _append_count_error(errors, "complex_step_total", counts["complex_step_total"], FROZEN_COMPLEX_STEP_TOTAL)
    _append_count_error(errors, "complex_step_range", tuple(counts["complex_step_range"]), FROZEN_COMPLEX_STEP_RANGE)
    _append_count_error(errors, "catalog_digest", catalog_digest(), FROZEN_CATALOG_DIGEST)
    return errors
