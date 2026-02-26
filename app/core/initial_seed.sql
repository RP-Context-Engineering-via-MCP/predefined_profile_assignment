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
-- 5. PROFILES (with full AI context)
-- =====================================================
INSERT INTO profile (profile_id, profile_name, description, context_statement, assumptions, ai_guidance, preferred_response_style, context_injection_prompt) VALUES
(
    'P1', 
    'Knowledge Seeker', 
    'Learns concepts and seeks explanations',
    'This user wants to understand.',
    '["User values clarity over speed", "Explanations are more important than final answers", "Users may ask follow-ups"]',
    '["Explain concepts step-by-step", "Use examples and analogies", "Avoid skipping reasoning", "Encourage learning, not just results"]',
    '["Educational", "Structured", "Patient", "Concept-first"]',
    'Respond as a tutor. Prioritize explanation and understanding.'
),
(
    'P2', 
    'Productivity Professional', 
    'Uses LLMs for efficient task completion',
    'This user wants results, fast.',
    '["User already understands basics", "Efficiency matters more than theory", "Output must be usable immediately"]',
    '["Be concise and direct", "Deliver ready-to-use outputs", "Follow requested formats strictly", "Minimize unnecessary explanation"]',
    '["Action-oriented", "Clear and structured", "Output-first"]',
    'Respond as an assistant focused on execution and efficiency.'
),
(
    'P3', 
    'Technical Problem Solver', 
    'Solves technical and engineering problems',
    'This user wants to solve complex problems.',
    '["Users are technically competent", "User cares about correctness and edge cases", "Iteration and refinement are expected"]',
    '["Analyze before answering", "Explain trade-offs and assumptions", "Consider edge cases and failure modes", "Support debugging and optimization"]',
    '["Analytical", "Precise", "Detailed where necessary"]',
    'Respond as a technical expert. Prioritize correctness and depth.'
),
(
    'P4', 
    'Creative Generator', 
    'Generates creative ideas and content',
    'This user wants ideas and creativity.',
    '["No single right answer", "Variety is more valuable than precision", "Exploration is encouraged"]',
    '["Generate multiple options", "Be imaginative and flexible", "Encourage creative variation", "Avoid overly rigid structure"]',
    '["Expressive", "Open-ended", "Inspiring"]',
    'Respond creatively. Prioritize originality and idea generation.'
),
(
    'P5', 
    'Lifestyle Advisor Seeker', 
    'Seeks personal and lifestyle guidance',
    'This user wants personal guidance.',
    '["User context and emotions matter", "Advice should be balanced and empathetic", "User seeks reassurance or direction"]',
    '["Be supportive and empathetic", "Ask clarifying questions when needed", "Avoid overly authoritative tone", "Provide balanced, actionable advice"]',
    '["Empathetic", "Encouraging", "Thoughtful"]',
    'Respond as a supportive advisor, not a command-giver.'
),
(
    'P6', 
    'Casual Explorer', 
    'Uses LLMs casually for curiosity or fun',
    'This user is here for light engagement.',
    '["User has low commitment", "Overly detailed responses reduce engagement", "Fun and accessibility matter"]',
    '["Keep responses short and friendly", "Avoid heavy structure or depth", "Match the users casual tone", "Optimize for enjoyment"]',
    '["Light", "Friendly", "Conversational"]',
    'Respond casually and keep things engaging and simple.'
)
ON CONFLICT (profile_id) DO UPDATE SET
    profile_name = EXCLUDED.profile_name,
    description = EXCLUDED.description,
    context_statement = EXCLUDED.context_statement,
    assumptions = EXCLUDED.assumptions,
    ai_guidance = EXCLUDED.ai_guidance,
    preferred_response_style = EXCLUDED.preferred_response_style,
    context_injection_prompt = EXCLUDED.context_injection_prompt;

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

-- =====================================================
-- 12. OUTPUT PREFERENCES
-- =====================================================
-- Controls how responses are structured and delivered
INSERT INTO output_preference (format_name, description) VALUES
('STEP_BY_STEP', 'Explain concepts progressively with ordered steps'),
('BULLET_POINTS', 'Concise bullet-pointed output'),
('CODE_FIRST', 'Prioritize code examples before explanation'),
('MULTI_OPTION', 'Provide multiple alternatives or variations'),
('SHORT_RESPONSE', 'Brief, minimal responses'),
('DETAILED_RESPONSE', 'In-depth explanations with detail')
ON CONFLICT (format_name) DO NOTHING;

-- =====================================================
-- 13. PROFILE → OUTPUT PREFERENCE
-- =====================================================
-- Maps stable response preferences per profile
INSERT INTO profile_output_preference (profile_id, output_pref_id, weight) VALUES
-- P1 Knowledge Seeker
('P1', 1, 1.0), -- STEP_BY_STEP
('P1', 6, 0.8), -- DETAILED_RESPONSE

-- P2 Productivity Professional
('P2', 2, 1.0), -- BULLET_POINTS
('P2', 5, 0.9), -- SHORT_RESPONSE

-- P3 Technical Problem Solver
('P3', 3, 1.0), -- CODE_FIRST
('P3', 6, 0.9), -- DETAILED_RESPONSE

-- P4 Creative Generator
('P4', 4, 1.0), -- MULTI_OPTION

-- P5 Lifestyle Advisor Seeker
('P5', 2, 0.8), -- BULLET_POINTS
('P5', 6, 0.7), -- DETAILED_RESPONSE

-- P6 Casual Explorer
('P6', 5, 1.0)  -- SHORT_RESPONSE
ON CONFLICT DO NOTHING;

-- =====================================================
-- 14. INTERACTION TONE
-- =====================================================
-- Controls voice, empathy, and response feel
INSERT INTO interaction_tone (tone_name, description) VALUES
('INSTRUCTIONAL', 'Teaching-focused, explanatory tone'),
('PROFESSIONAL', 'Direct, task-oriented professional tone'),
('PRECISE', 'Accuracy-first, technical tone'),
('CREATIVE', 'Open, imaginative, expressive tone'),
('EMPATHETIC', 'Supportive, understanding tone'),
('FRIENDLY', 'Light, conversational tone')
ON CONFLICT (tone_name) DO NOTHING;

-- =====================================================
-- 15. PROFILE → INTERACTION TONE
-- =====================================================
-- Defines default tone per profile
INSERT INTO profile_tone (profile_id, tone_id, weight) VALUES
-- P1 Knowledge Seeker
('P1', 1, 1.0), -- INSTRUCTIONAL

-- P2 Productivity Professional
('P2', 2, 1.0), -- PROFESSIONAL

-- P3 Technical Problem Solver
('P3', 3, 1.0), -- PRECISE

-- P4 Creative Generator
('P4', 4, 1.0), -- CREATIVE

-- P5 Lifestyle Advisor Seeker
('P5', 5, 1.0), -- EMPATHETIC

-- P6 Casual Explorer
('P6', 6, 1.0)  -- FRIENDLY
ON CONFLICT DO NOTHING;

-- =====================================================
-- 16. DOMAIN EXPERTISE LEVEL
-- =====================================================
-- Defines possible expertise states (NOT profiles)
INSERT INTO domain_expertise_level (level_name, description) VALUES
('BEGINNER', 'Limited prior knowledge, needs explanation'),
('INTERMEDIATE', 'Understands fundamentals, wants applied detail'),
('ADVANCED', 'High proficiency, expects precision and optimization')
ON CONFLICT (level_name) DO NOTHING;