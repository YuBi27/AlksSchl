-- Очищення БД: залишити лише адміна (telegram_id = 393283031)
-- Видаляємо всі пов'язані дані користувачів, крім адміна

BEGIN;

-- Зберігаємо ID адміна
DO $$
DECLARE
    admin_telegram_id BIGINT := 393283031;
    admin_user_id INT;
BEGIN
    SELECT id INTO admin_user_id FROM users WHERE telegram_id = admin_telegram_id;
    RAISE NOTICE 'Admin user_id: %', admin_user_id;

    -- Видаляємо quiz_answers -> quiz_attempts -> quiz_assignments для не-адмінів
    DELETE FROM quiz_answers
    WHERE attempt_id IN (
        SELECT id FROM quiz_attempts
        WHERE student_user_id IN (SELECT id FROM users WHERE telegram_id != admin_telegram_id)
    );

    DELETE FROM quiz_attempts
    WHERE student_user_id IN (SELECT id FROM users WHERE telegram_id != admin_telegram_id);

    DELETE FROM quiz_assignments
    WHERE student_user_id IN (SELECT id FROM users WHERE telegram_id != admin_telegram_id);

    -- Видаляємо homework_grades для не-адмінів
    DELETE FROM homework_grades
    WHERE student_user_id IN (SELECT id FROM users WHERE telegram_id != admin_telegram_id);

    -- Видаляємо attendances для не-адмінів
    DELETE FROM attendances
    WHERE student_user_id IN (SELECT id FROM users WHERE telegram_id != admin_telegram_id);

    -- Видаляємо teacher_notes для не-адмінів
    DELETE FROM teacher_notes
    WHERE student_user_id IN (SELECT id FROM users WHERE telegram_id != admin_telegram_id);

    -- Видаляємо student_groups для не-адмінів
    DELETE FROM student_groups
    WHERE user_id IN (SELECT id FROM users WHERE telegram_id != admin_telegram_id);

    -- Видаляємо agreements для не-адмінів
    DELETE FROM agreements
    WHERE user_id IN (SELECT id FROM users WHERE telegram_id != admin_telegram_id);

    -- Видаляємо homeworks де teacher_id або student_user_id — не адмін
    DELETE FROM homeworks
    WHERE student_user_id IN (SELECT id FROM users WHERE telegram_id != admin_telegram_id);

    -- Видаляємо admin_actions_log що посилаються на не-адмінів
    DELETE FROM admin_actions_log
    WHERE (admin_id IN (SELECT id FROM users WHERE telegram_id != admin_telegram_id)
        OR target_user_id IN (SELECT id FROM users WHERE telegram_id != admin_telegram_id));

    -- Видаляємо invite_codes що були використані не-адмінами
    UPDATE invite_codes SET used_by = NULL, used_at = NULL
    WHERE used_by IN (SELECT id FROM users WHERE telegram_id != admin_telegram_id);

    DELETE FROM invite_codes
    WHERE created_by IN (SELECT id FROM users WHERE telegram_id != admin_telegram_id);

    -- Видаляємо payments для не-адмінів
    DELETE FROM payments
    WHERE user_id IN (SELECT id FROM users WHERE telegram_id != admin_telegram_id);

    -- Нарешті видаляємо самих користувачів (cascade видалить profiles і agreements)
    DELETE FROM users WHERE telegram_id != admin_telegram_id;

    RAISE NOTICE 'Cleanup done. Users remaining:';
END $$;

SELECT id, telegram_id, username, role, status FROM users;

COMMIT;
