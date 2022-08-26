-- Add table to store suggestions. Introduced in
-- https://phabricator.wikimedia.org/T312949

CREATE TABLE suggestion (
    id INT NOT NULL AUTO_INCREMENT,
    id INT  NOT NULL PRIMARY KEY AUTO_INCREMENT,
    depict_item VARCHAR(15),
    file_name VARCHAR(240) NOT NULL,
    update_status INT DEFAULT 0,
    google_vision INT DEFAULT 0,
    metadata_to_concept INT DEFAULT 0,
    google_vision_confidence FLOAT,
    metadata_to_concept_confidence FLOAT,
    campaign_id INT NOT NULL,
    user_id INT NOT NULL,
        PRIMARY KEY (id),
        FOREIGN KEY (campaign_id) REFERENCES campaign(id),
        FOREIGN KEY (user_id) REFERENCES user(id)
);
