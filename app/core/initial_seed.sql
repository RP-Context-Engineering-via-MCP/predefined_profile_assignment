-- =====================================================
-- 1. INTENTS
-- =====================================================
INSERT INTO intent (intent_id, intent_name, description) VALUES
(1, 'LEARNING', 'Cognitive support, gaining knowledge or understanding'),
(2, 'TASK_COMPLETION', 'Completing tasks efficiently and effectively'),
(3, 'PROBLEM_SOLVING', 'Solving technical problems accurately'),
(4, 'EXPLORATION', 'Generating ideas and creative outputs'),
(5, 'GUIDANCE', 'Seeking advice for personal or lifestyle decisions'),
(6, 'ENGAGEMENT', 'Entertainment, casual use, curiosity')
ON CONFLICT (intent_id) DO NOTHING;

-- =====================================================
-- 2. BEHAVIOR LEVELS
-- =====================================================
INSERT INTO behavior_level (behavior_level_id, level_name, description) VALUES
(1, 'BASIC', 'Simple prompts, low iteration, shallow engagement'),
(2, 'INTERMEDIATE', 'Moderate complexity, task-based, some iteration'),
(3, 'ADVANCED', 'Structured prompts, iterative workflows, automation')
ON CONFLICT (behavior_level_id) DO NOTHING;

-- =====================================================
-- 3. INTEREST AREAS
-- =====================================================
INSERT INTO interest_area (interest_id, interest_name, description) VALUES
(1, 'AI', 'Artificial Intelligence and machine learning'),
(2, 'DATA_SCIENCE', 'Data analysis and science'),
(3, 'WRITING', 'Drafting, editing, summarizing content'),
(4, 'PROGRAMMING', 'Coding, debugging, algorithms'),
(5, 'CREATIVE', 'Stories, scripts, blogs, ideation'),
(6, 'HEALTH', 'Well-being, diet, exercise'),
(7, 'PERSONAL_GROWTH', 'Career, life, and self-growth guidance'),
(8, 'ENTERTAINMENT', 'Games, quizzes, leisure activities')
ON CONFLICT (interest_id) DO NOTHING;

-- =====================================================
-- 4. BEHAVIOR SIGNALS
-- =====================================================
INSERT INTO behavior_signal (signal_id, signal_name, description) VALUES
(1, 'DEEP_REASONING', 'Open-ended learning or curiosity-driven queries'),
(2, 'GOAL_ORIENTED', 'Command-based or goal-oriented prompts'),
(3, 'MULTI_STEP', 'Prompts with multiple steps or constraints'),
(4, 'ITERATIVE', 'User refines or follows up repeatedly'),
(5, 'CASUAL', 'Short, low-effort, entertainment-focused prompts')
ON CONFLICT (signal_id) DO NOTHING;

-- =====================================================
-- 5. PROFILES
-- =====================================================
INSERT INTO profile (profile_id, profile_name, description) VALUES
('P1', 'Knowledge Seeker', 'Learns concepts and seeks explanations'),
('P2', 'Productivity Professional', 'Uses LLMs for efficient task completion'),
('P3', 'Technical Problem Solver', 'Solves technical and engineering problems'),
('P4', 'Creative Generator', 'Generates creative ideas and content'),
('P5', 'Lifestyle Advisor Seeker', 'Seeks personal and lifestyle guidance'),
('P6', 'Casual Explorer', 'Uses LLMs casually for curiosity or fun')
ON CONFLICT (profile_id) DO NOTHING;

-- =====================================================
-- 6. PROFILE_INTENT
-- =====================================================
INSERT INTO profile_intent (profile_id, intent_id, is_primary, weight) VALUES
('P1', 1, TRUE, 1.0),
('P2', 2, TRUE, 1.0),
('P3', 3, TRUE, 1.0),
('P4', 4, TRUE, 1.0),
('P5', 5, TRUE, 1.0),
('P6', 6, TRUE, 1.0)
ON CONFLICT DO NOTHING;

-- =====================================================
-- 7. PROFILE_INTEREST
-- =====================================================
INSERT INTO profile_interest (profile_id, interest_id, weight) VALUES
('P1', 1, 0.9),
('P1', 2, 0.8),

('P2', 3, 1.0),
('P2', 2, 0.7),

('P3', 1, 1.0),
('P3', 4, 0.8),

('P4', 5, 1.0),
('P4', 3, 0.6),

('P5', 6, 0.8),
('P5', 7, 1.0),

('P6', 8, 1.0)
ON CONFLICT DO NOTHING;

-- =====================================================
-- 8. PROFILE_BEHAVIOR_LEVEL
-- =====================================================
INSERT INTO profile_behavior_level (profile_id, behavior_level_id) VALUES
('P1', 1), ('P1', 2), ('P1', 3),
('P2', 2),
('P3', 3),
('P4', 2),
('P5', 1), ('P5', 2),
('P6', 1)
ON CONFLICT DO NOTHING;

-- =====================================================
-- 9. PROFILE_BEHAVIOR_SIGNAL
-- =====================================================
INSERT INTO profile_behavior_signal (profile_id, signal_id, weight) VALUES
('P1', 1, 1.0),

('P2', 2, 1.0),
('P2', 3, 0.6),

('P3', 3, 1.0),
('P3', 4, 1.0),

('P4', 4, 1.0),

('P5', 1, 0.8),

('P6', 5, 1.0)
ON CONFLICT DO NOTHING;

-- =====================================================
-- 10. STANDARD MATCHING FACTORS
-- =====================================================
-- Weights for standard mode (full behavioral analysis with all factors)
INSERT INTO standard_matching_factor (factor_name, weight) VALUES
('INTENT', 0.35),
('INTEREST', 0.25),
('COMPLEXITY', 0.15),
('STYLE', 0.15),
('CONSISTENCY', 0.10)
ON CONFLICT (factor_name) DO NOTHING;

-- =====================================================
-- 11. COLD-START MATCHING FACTORS
-- =====================================================
-- Weights for cold-start mode (simplified matching for new users)
INSERT INTO cold_start_matching_factor (factor_name, weight) VALUES
('INTENT', 0.60),
('INTEREST', 0.40),
('COMPLEXITY', 0.00),
('STYLE', 0.00),
('CONSISTENCY', 0.00)
ON CONFLICT (factor_name) DO NOTHING;