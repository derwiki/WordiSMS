CREATE TABLE IF NOT EXISTS `www_contact` (
  `id` int(11) NOT NULL auto_increment,
  `address` varchar(50) NOT NULL,
  `type` varchar(25) NOT NULL,
  `verbose` tinyint(1) NOT NULL,
  `time_created` datetime NOT NULL,
  `token` int(10) unsigned NOT NULL,
  `wordisms_user_id` int(11) default NULL,
  PRIMARY KEY  (`id`),
  UNIQUE KEY `address` (`address`,`type`),
  KEY `www_contact_wordisms_user_id` (`wordisms_user_id`)
) ENGINE=MyISAM  DEFAULT CHARSET=latin1;

insert into `www_contact` (id, address, type, verbose, time_created, token, wordisms_user_id) (select id, phonenumber address, "email", 0, time_created, 11111, NULL from main_user order by id asc);

RENAME TABLE `wordisms`.`main_dictionary`  TO `wordisms`.`www_dictionaryentry` ;
update `wordisms`.`www_dictionaryentry` set wordlist_id=1;

RENAME TABLE `wordisms`.`main_questions`  TO `wordisms`.`www_questions` ;
ALTER TABLE `www_questions` CHANGE `user_id` `contact_id` INT( 11 ) NOT NULL  

CREATE TABLE IF NOT EXISTS `www_responses` (
  `id` int(11) NOT NULL auto_increment,
  `timestamp` datetime NOT NULL,
  `definition_id` int(11) NOT NULL,
  `word_id` int(11) NOT NULL,
  `contact_id` int(11) NOT NULL,
  PRIMARY KEY  (`id`),
  KEY `www_responses_definition_id` (`definition_id`),
  KEY `www_responses_word_id` (`word_id`),
  KEY `www_responses_contact_id` (`contact_id`)
) ENGINE=MyISAM  DEFAULT CHARSET=latin1;

insert into `wordisms`.`www_responses` (id, timestamp, definition_id, word_id, contact_id) (select id, timestamp, def_uid_id, word_uid_id, user_uid_id from `wordisms`.`main_submitted`);

