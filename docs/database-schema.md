# HavenJob -- Database Schema

This version incorporates architectural improvements following formal
schema review.\
Enhancements focus on stronger data integrity, scalability, search
performance, and future-proofing.

------------------------------------------------------------------------

# 1. Authentication & Onboarding

## users

  Column                       Type                            Notes
  ---------------------------- ------------------------------- -------
  id                           UUID PK                         
  email                        String UNIQUE NOT NULL          
  hashed_password              String Nullable                 
  auth_provider                Enum(email, google, linkedin)   
  forwarding_address           String UNIQUE NOT NULL          
  full_name                    String Nullable                 
  target_role                  String Nullable                 
  skills                       JSONB Nullable                  
  avatar_url                   String Nullable                 
  onboarding_completed         Boolean Default false           
  profile_completion_percent   Integer Default 0               
  subscription_tier            Enum(free, credits, pro) Default free    Cloud only; ignored on self-hosted
  credits_balance              Integer Default 0               Cloud only; deducted per AI/email call
  created_at                   Timestamp                       
  updated_at                   Timestamp                       
  deleted_at                   Timestamp Nullable              

------------------------------------------------------------------------

## trusted_senders

  Column         Type                                   Notes
  -------------- -------------------------------------- -------
  id             UUID PK                                
  user_id        UUID FK → users.id ON DELETE CASCADE   
  sender_email   String NOT NULL                        
  label          String Nullable                        e.g., "My Gmail", "LinkedIn"
  created_at     Timestamp                              

### Constraints

-   UNIQUE(user_id, sender_email)

------------------------------------------------------------------------

## user_provider_settings
Stores the user's chosen LLM and email inbound provider, plus their encrypted API key.

  Column              Type                                                  Notes
  ------------------- ----------------------------------------------------- -------
  id                  UUID PK                                               
  user_id             UUID FK → users.id ON DELETE CASCADE                  
  provider_type       Enum(llm, email_inbound)                              
  provider_name       Enum(openai, anthropic, gmail, sendgrid)              
  encrypted_api_key   String Nullable                                       Encrypted at rest (e.g., AES via cryptography lib or AWS KMS)
  created_at          Timestamp                                             
  updated_at          Timestamp                                             

### Constraints

-   UNIQUE(user_id, provider_type) — one active provider per type per user

------------------------------------------------------------------------

# 2. Job Tracker

## applications

  ------------------------------------------------------------------------
  Column                      Type                 Notes
  --------------------------- -------------------- -----------------------
  id                          UUID PK              

  user_id                     UUID FK → users.id   
                              ON DELETE CASCADE    

  company_name                String NOT NULL      

  job_title                   String NOT NULL      

  date_applied                Timestamp NOT NULL   

  deadline                    Timestamp Nullable   

  follow_up_date              Timestamp Nullable   

  status                      Enum (Applied, Under 
                              Review, Phone        
                              Screen, Interview,   
                              Offer, Accepted,     
                              Rejected, Withdrawn) 

  source                      String Nullable      

  job_url                     String Nullable      

  location                    String Nullable      

  salary_min                  Integer Nullable     

  salary_max                  Integer Nullable     

  salary_currency             String(3) Nullable   

  notes                       Text Nullable        

  is_needs_review             Boolean Default      
                              false                

  confidence_score            Float Nullable       

  parse_metadata              JSONB Nullable       

  raw_email_hash              String Nullable      

  created_at                  Timestamp            

  updated_at                  Timestamp            

  deleted_at                  Timestamp Nullable   
  ------------------------------------------------------------------------

### Indexes

-   (user_id, status)
-   (user_id, date_applied DESC)
-   (user_id, follow_up_date)
-   Full-text GIN index on (company_name, job_title)

### Constraints

-   UNIQUE(user_id, raw_email_hash) WHERE raw_email_hash IS NOT NULL

------------------------------------------------------------------------

## application_status_history

  Column           Type                                          Notes
  ---------------- --------------------------------------------- -------
  id               UUID PK                                       
  application_id   UUID FK → applications.id ON DELETE CASCADE   
  old_status       Enum Nullable                                 
  new_status       Enum NOT NULL                                 
  changed_by       Enum(user, email_parser, system)              
  changed_at       Timestamp Default NOW                         

------------------------------------------------------------------------

# 3. Notifications

## notifications

  Column                Type                                          Notes
  --------------------- --------------------------------------------- -------
  id                    UUID PK                                       
  user_id               UUID FK → users.id ON DELETE CASCADE          
  type                  Enum                                          
  title                 String NOT NULL                               
  message               Text Nullable                                 
  is_read               Boolean Default false                         
  is_email_sent         Boolean Default false                         
  related_entity_type   Enum(application, system, billing) Nullable   
  related_entity_id     UUID Nullable                                 
  created_at            Timestamp                                     

### Indexes

-   (user_id, is_read)

------------------------------------------------------------------------

# 4. AI Career Assistant

## education

  Column           Type                                   Notes
  ---------------- -------------------------------------- -------
  id               UUID PK                                
  user_id          UUID FK → users.id ON DELETE CASCADE   
  institution      String NOT NULL                        
  degree           String NOT NULL                        
  field_of_study   String Nullable                        
  start_date       Date                                   
  end_date         Date Nullable                          
  is_current       Boolean Default false                  
  grade            String Nullable                        
  display_order    Integer Default 0                      
  created_at       Timestamp                              
  updated_at       Timestamp                              

------------------------------------------------------------------------

## work_experiences

  Column          Type                                   Notes
  --------------- -------------------------------------- -------
  id              UUID PK                                
  user_id         UUID FK → users.id ON DELETE CASCADE   
  company         String NOT NULL                        
  role            String NOT NULL                        
  start_date      Date                                   
  end_date        Date Nullable                          
  is_current      Boolean Default false                  
  description     Text Nullable                          
  display_order   Integer Default 0                      
  created_at      Timestamp                              
  updated_at      Timestamp                              
  deleted_at      Timestamp Nullable                     

------------------------------------------------------------------------

## projects

  Column          Type                                   Notes
  --------------- -------------------------------------- -------
  id              UUID PK                                
  user_id         UUID FK → users.id ON DELETE CASCADE   
  title           String NOT NULL                        
  description     Text NOT NULL                          
  technologies    JSONB Nullable                         
  url             String Nullable                        
  display_order   Integer Default 0                      
  created_at      Timestamp                              
  updated_at      Timestamp                              
  deleted_at      Timestamp Nullable                     

------------------------------------------------------------------------

## cv_documents

  Column        Type                                   Notes
  ------------- -------------------------------------- -------
  id            UUID PK                                
  user_id       UUID FK → users.id ON DELETE CASCADE   
  file_name     String NOT NULL                        
  file_url      String NOT NULL                        
  parsed_text   Text Nullable                          
  is_primary    Boolean Default false                  
  uploaded_at   Timestamp                              
  deleted_at    Timestamp Nullable                     

### Constraints

-   UNIQUE(user_id) WHERE is_primary = true

------------------------------------------------------------------------

## job_descriptions

  Column           Type                                   Notes
  ---------------- -------------------------------------- -------
  id               UUID PK                                
  user_id          UUID FK → users.id ON DELETE CASCADE   
  application_id   UUID FK → applications.id Nullable     
  company_name     String Nullable                        
  job_title        String Nullable                        
  raw_text         Text NOT NULL                          
  content_hash     String Nullable                        
  created_at       Timestamp                              
  updated_at       Timestamp                              

### Indexes

-   content_hash (for deduplication lookups)

### Constraints

-   UNIQUE(user_id, content_hash) WHERE content_hash IS NOT NULL

------------------------------------------------------------------------

## interview_questions

  Column          Type                          Notes
  --------------- ----------------------------- -------
  id              UUID PK                       
  category        String NOT NULL               
  question_type   Enum(behavioural, standard)   
  question        Text NOT NULL                 
  created_at      Timestamp                     

------------------------------------------------------------------------

## user_answers

  Column               Type                                        Notes
  -------------------- ------------------------------------------- -------
  id                   UUID PK                                     
  user_id              UUID FK → users.id ON DELETE CASCADE        
  question_id          UUID FK → interview_questions.id Nullable   
  custom_question      Text Nullable                               
  draft_answer         Text Nullable                               
  ai_improved_answer   Text Nullable                               
  is_ai_generated      Boolean Default false                       
  created_at           Timestamp                                   
  updated_at           Timestamp                                   

### Constraints

-   CHECK (question_id IS NOT NULL OR custom_question IS NOT NULL)

------------------------------------------------------------------------

## chat_sessions

  Column       Type                                   Notes
  ------------ -------------------------------------- -------
  id           UUID PK                                
  user_id      UUID FK → users.id ON DELETE CASCADE   
  title        String Nullable                        
  created_at   Timestamp                              
  updated_at   Timestamp                              

------------------------------------------------------------------------

## chat_messages

  Column        Type                                           Notes
  ------------- ---------------------------------------------- -------
  id            UUID PK                                        
  session_id    UUID FK → chat_sessions.id ON DELETE CASCADE   
  role          Enum(user, assistant, system)                  
  content       Text NOT NULL                                  
  token_count   Integer Nullable                               
  created_at    Timestamp                                      

### Indexes

-   (session_id, created_at)

------------------------------------------------------------------------

# 5. Supporting Tables

## user_notification_preferences

  Column                         Type                                   Notes
  ------------------------------ -------------------------------------- -------
  id                             UUID PK                                
  user_id                        UUID FK → users.id ON DELETE CASCADE   
  email_notifications_enabled    Boolean Default true                   
  in_app_notifications_enabled   Boolean Default true                   
  created_at                     Timestamp                              
  updated_at                     Timestamp                              

------------------------------------------------------------------------

## ai_outputs
Stores all AI-generated content so users can retrieve and reuse previous outputs.

  Column                Type                                              Notes
  --------------------- ------------------------------------------------- -------
  id                    UUID PK                                           
  user_id               UUID FK → users.id ON DELETE CASCADE              
  type                  Enum(cover_letter, tailored_cv, question_answer)  
  job_description_id    UUID FK → job_descriptions.id Nullable            
  application_id        UUID FK → applications.id Nullable                
  content               Text NOT NULL                                     The generated output
  prompt_snapshot       Text Nullable                                     Optional: store the prompt used
  created_at            Timestamp                                         

### Indexes

-   (user_id, type)
-   (user_id, created_at DESC)

------------------------------------------------------------------------

# End of v2.1 Schema
