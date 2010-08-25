insert into www_contact (id, address, type, time_created) (select id, phonenumber address, "email" type, time_created from main_user)

insert into www_responses (timestamp, definition_id, word_id, contact_id) (select timestamp, def_uid_id, word_uid_id, user_uid_id from main_submitted)

insert into www_questions (user_id, correct_id, one_id, two_id, three_id, four_id, time_created) (select user_id, correct_id, one_id, two_id, three_id, four_id, time_created from main_questions)

insert into www_questions (user_id, correct_id, one_id, two_id, three_id, four_id, time_created) (select user_id, correct_id, one_id, two_id, three_id, four_id, time_created from main_questions)
