--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: data_sets; Type: TABLE; Schema: public; Owner: testuser; Tablespace: 
--

CREATE TABLE data_sets (
    id integer NOT NULL,
    name character varying(50) NOT NULL,
    query text NOT NULL
);


ALTER TABLE public.data_sets OWNER TO testuser;

--
-- Name: data_sets_id_seq; Type: SEQUENCE; Schema: public; Owner: testuser
--

CREATE SEQUENCE data_sets_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.data_sets_id_seq OWNER TO testuser;

--
-- Name: data_sets_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: testuser
--

ALTER SEQUENCE data_sets_id_seq OWNED BY data_sets.id;


--
-- Name: survey_questions; Type: TABLE; Schema: public; Owner: testuser; Tablespace: 
--

CREATE TABLE survey_questions (
    id integer NOT NULL,
    question_text text NOT NULL,
    input_type character varying(50) NOT NULL,
    response_type character varying(10),
    parent_question integer,
    survey_id integer NOT NULL
);


ALTER TABLE public.survey_questions OWNER TO testuser;

--
-- Name: survey_questions_id_seq; Type: SEQUENCE; Schema: public; Owner: testuser
--

CREATE SEQUENCE survey_questions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.survey_questions_id_seq OWNER TO testuser;

--
-- Name: survey_questions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: testuser
--

ALTER SEQUENCE survey_questions_id_seq OWNED BY survey_questions.id;


--
-- Name: survey_responses; Type: TABLE; Schema: public; Owner: testuser; Tablespace: 
--

CREATE TABLE survey_responses (
    id integer NOT NULL,
    value character varying(150) NOT NULL,
    question_id integer NOT NULL
);


ALTER TABLE public.survey_responses OWNER TO testuser;

--
-- Name: survey_responses_id_seq; Type: SEQUENCE; Schema: public; Owner: testuser
--

CREATE SEQUENCE survey_responses_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.survey_responses_id_seq OWNER TO testuser;

--
-- Name: survey_responses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: testuser
--

ALTER SEQUENCE survey_responses_id_seq OWNED BY survey_responses.id;


--
-- Name: surveys; Type: TABLE; Schema: public; Owner: testuser; Tablespace: 
--

CREATE TABLE surveys (
    id integer NOT NULL,
    name character varying(10) NOT NULL
);


ALTER TABLE public.surveys OWNER TO testuser;

--
-- Name: surveys_id_seq; Type: SEQUENCE; Schema: public; Owner: testuser
--

CREATE SEQUENCE surveys_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.surveys_id_seq OWNER TO testuser;

--
-- Name: surveys_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: testuser
--

ALTER SEQUENCE surveys_id_seq OWNED BY surveys.id;


--
-- Name: user_responses; Type: TABLE; Schema: public; Owner: testuser; Tablespace: 
--

CREATE TABLE user_responses (
    value text,
    comment text,
    id integer NOT NULL,
    user_id integer,
    question_id integer,
    response_id integer,
    "timestamp" timestamp without time zone
);


ALTER TABLE public.user_responses OWNER TO testuser;

--
-- Name: user_responses_id_seq; Type: SEQUENCE; Schema: public; Owner: testuser
--

CREATE SEQUENCE user_responses_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.user_responses_id_seq OWNER TO testuser;

--
-- Name: user_responses_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: testuser
--

ALTER SEQUENCE user_responses_id_seq OWNED BY user_responses.id;


--
-- Name: user_tile_selections; Type: TABLE; Schema: public; Owner: testuser; Tablespace: 
--

CREATE TABLE user_tile_selections (
    id integer NOT NULL,
    tile_id text NOT NULL,
    zoom_level integer NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    query text NOT NULL,
    image text,
    x_label character varying,
    y_label character varying,
    z_label character varying,
    x_inv boolean,
    y_inv boolean,
    z_inv boolean,
    color character varying(100),
    width integer,
    height integer,
    user_id integer NOT NULL,
    dataset_id integer
);


ALTER TABLE public.user_tile_selections OWNER TO testuser;

--
-- Name: user_tile_selections_id_seq; Type: SEQUENCE; Schema: public; Owner: testuser
--

CREATE SEQUENCE user_tile_selections_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.user_tile_selections_id_seq OWNER TO testuser;

--
-- Name: user_tile_selections_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: testuser
--

ALTER SEQUENCE user_tile_selections_id_seq OWNED BY user_tile_selections.id;


--
-- Name: user_tile_updates; Type: TABLE; Schema: public; Owner: testuser; Tablespace: 
--

CREATE TABLE user_tile_updates (
    id integer NOT NULL,
    tile_id text NOT NULL,
    zoom_level integer NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    query text NOT NULL,
    x_label character varying,
    y_label character varying,
    z_label character varying,
    x_inv boolean,
    y_inv boolean,
    z_inv boolean,
    color character varying(100),
    width integer,
    height integer,
    user_id integer NOT NULL,
    dataset_id integer
);


ALTER TABLE public.user_tile_updates OWNER TO testuser;

--
-- Name: user_tile_updates_id_seq; Type: SEQUENCE; Schema: public; Owner: testuser
--

CREATE SEQUENCE user_tile_updates_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.user_tile_updates_id_seq OWNER TO testuser;

--
-- Name: user_tile_updates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: testuser
--

ALTER SEQUENCE user_tile_updates_id_seq OWNED BY user_tile_updates.id;


--
-- Name: user_traces; Type: TABLE; Schema: public; Owner: testuser; Tablespace: 
--

CREATE TABLE user_traces (
    id integer NOT NULL,
    tile_id text NOT NULL,
    zoom_level integer NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    query text NOT NULL,
    user_id integer NOT NULL,
    dataset_id integer
);


ALTER TABLE public.user_traces OWNER TO testuser;

--
-- Name: user_traces_id_seq; Type: SEQUENCE; Schema: public; Owner: testuser
--

CREATE SEQUENCE user_traces_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.user_traces_id_seq OWNER TO testuser;

--
-- Name: user_traces_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: testuser
--

ALTER SEQUENCE user_traces_id_seq OWNED BY user_traces.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: testuser; Tablespace: 
--

CREATE TABLE users (
    id integer NOT NULL,
    flask_session_id character varying(50) NOT NULL,
    done boolean
);


ALTER TABLE public.users OWNER TO testuser;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: testuser
--

CREATE SEQUENCE users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO testuser;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: testuser
--

ALTER SEQUENCE users_id_seq OWNED BY users.id;


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: testuser
--

ALTER TABLE ONLY data_sets ALTER COLUMN id SET DEFAULT nextval('data_sets_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: testuser
--

ALTER TABLE ONLY survey_questions ALTER COLUMN id SET DEFAULT nextval('survey_questions_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: testuser
--

ALTER TABLE ONLY survey_responses ALTER COLUMN id SET DEFAULT nextval('survey_responses_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: testuser
--

ALTER TABLE ONLY surveys ALTER COLUMN id SET DEFAULT nextval('surveys_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: testuser
--

ALTER TABLE ONLY user_responses ALTER COLUMN id SET DEFAULT nextval('user_responses_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: testuser
--

ALTER TABLE ONLY user_tile_selections ALTER COLUMN id SET DEFAULT nextval('user_tile_selections_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: testuser
--

ALTER TABLE ONLY user_tile_updates ALTER COLUMN id SET DEFAULT nextval('user_tile_updates_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: testuser
--

ALTER TABLE ONLY user_traces ALTER COLUMN id SET DEFAULT nextval('user_traces_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: testuser
--

ALTER TABLE ONLY users ALTER COLUMN id SET DEFAULT nextval('users_id_seq'::regclass);


--
-- Data for Name: data_sets; Type: TABLE DATA; Schema: public; Owner: testuser
--

COPY data_sets (id, name, query) FROM stdin;
1	ndsi	select * from ndsi_array
2	ndvi_us	select * from ndvi_us
3	us1000	select * from us1000
4	cali100	select * from cali100
5	us100	select * from us100
\.


--
-- Name: data_sets_id_seq; Type: SEQUENCE SET; Schema: public; Owner: testuser
--

SELECT pg_catalog.setval('data_sets_id_seq', 1, false);


--
-- Data for Name: survey_questions; Type: TABLE DATA; Schema: public; Owner: testuser
--

COPY survey_questions (id, question_text, input_type, response_type, parent_question, survey_id) FROM stdin;
1	Age:	text	number	\N	1
2	Gender:	select	\N	\N	1
3	Where are you from?	text	string	\N	1
4	Where are you located now?	text	string	\N	1
5	What is your occupation	text	string	\N	1
6	What is your level of computer experience?	select	\N	\N	1
7	What type of computer are you using?	select	\N	\N	1
8	What brand of computer are you using?	text	string	\N	1
9	What size of screen are you using?	text	string	\N	1
10	What operating system are you using right now?	text	string	\N	1
11	How many hours per day do you spend on a computer?	select	\N	\N	1
12	How often do you use the Internet?	select	\N	\N	1
13	Are you working on a public or personal computer?	select	\N	\N	1
15	For each statement below, please select the number that corresponds to your level of agreement with that statement:	select	\N	\N	2
16	The interaction style (buttons, menus, etc.) was appropriate for the task	select	\N	15	2
17	If given a choice, I would use this program to complete similar tasks in my daily life.	select	\N	15	2
18	The integration of the visualization with the user interface was seamless and lead to smooth interactions.	select	\N	15	2
19	The program was too slow to be practical.	select	\N	15	2
20	The visualization was aesthetically pleasing.	select	\N	15	2
21	The program responded quickly enough to allow me to complete the task at my own pace.	select	\N	15	2
22	The task took too long to complete.	select	\N	15	2
23	If this interface were part of a software program for performing similar tasks to the one performed today, I would recommend it to my friends/colleagues.	select	\N	15	2
24	I frequently had to wait for the program to load before continuing with the task.	select	\N	15	2
25	I enjoyed performing the task.	select	\N	15	2
26	The user interface was easy to use.	select	\N	15	2
27	I wanted the program to respond faster.	select	\N	15	2
28	Using the program was annoying and I did not enjoy it.	select	\N	15	2
29	I felt that the visualization was always available and loaded when I wanted to continue with the task.	select	\N	15	2
30	The program helped me to quickly complete the task.	select	\N	15	2
31	I felt that the program’s response time interfered with my ability to complete the task in a timely manner.	select	\N	15	2
32	The visualization was an interesting representation of data.	select	\N	15	2
33	The interface design was cohesive and visually pleasing.	select	\N	15	2
34	The user interface was clumsy and slow.	select	\N	15	2
35	The computer response time was too slow for me to be able to complete the task in a reasonable amount of time.	select	\N	15	2
36	Please provide any additional comments you have about the visualization tool below:	textbox	string	\N	2
14	What kinds of computing devices do you own or frequently use? (Select all that apply)	multiple	\N	\N	1
\.


--
-- Name: survey_questions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: testuser
--

SELECT pg_catalog.setval('survey_questions_id_seq', 1, false);


--
-- Data for Name: survey_responses; Type: TABLE DATA; Schema: public; Owner: testuser
--

COPY survey_responses (id, value, question_id) FROM stdin;
1	Female	2
2	Male	2
3	Novice	6
4	Experienced beginner	6
5	Intermediate user	6
6	Experienced user	6
7	Expert	6
8	Desktop	7
9	Laptop	7
10	Tablet/iPad	7
11	Smart phone	7
12	Other	7
13	Less than 1 hour	11
14	Between 1 and 3 hours	11
15	Between 3 and 5 hours	11
16	Between 5 and 8 hours	11
17	More than 8 hours	11
18	Monthly	12
19	Weekly	12
20	Daily	12
21	Hourly	12
22	Personal	13
23	Public	13
24	Desktop	14
25	Laptop	14
26	Tablet/iPad	14
27	Smart phone	14
28	Other	14
29	Strongly disagree	15
30	Disagree	15
31	Neutral	15
32	Agree	15
33	Strongly agree	15
\.


--
-- Name: survey_responses_id_seq; Type: SEQUENCE SET; Schema: public; Owner: testuser
--

SELECT pg_catalog.setval('survey_responses_id_seq', 1, false);


--
-- Data for Name: surveys; Type: TABLE DATA; Schema: public; Owner: testuser
--

COPY surveys (id, name) FROM stdin;
1	pre
2	post
\.


--
-- Name: surveys_id_seq; Type: SEQUENCE SET; Schema: public; Owner: testuser
--

SELECT pg_catalog.setval('surveys_id_seq', 1, false);


--
-- Data for Name: user_responses; Type: TABLE DATA; Schema: public; Owner: testuser
--

COPY user_responses (value, comment, id, user_id, question_id, response_id, "timestamp") FROM stdin;
\.


--
-- Name: user_responses_id_seq; Type: SEQUENCE SET; Schema: public; Owner: testuser
--

SELECT pg_catalog.setval('user_responses_id_seq', 1, false);


--
-- Data for Name: user_tile_selections; Type: TABLE DATA; Schema: public; Owner: testuser
--

COPY user_tile_selections (id, tile_id, zoom_level, "timestamp", query, image, x_label, y_label, z_label, x_inv, y_inv, z_inv, color, width, height, user_id, dataset_id) FROM stdin;
\.


--
-- Name: user_tile_selections_id_seq; Type: SEQUENCE SET; Schema: public; Owner: testuser
--

SELECT pg_catalog.setval('user_tile_selections_id_seq', 1, false);


--
-- Data for Name: user_tile_updates; Type: TABLE DATA; Schema: public; Owner: testuser
--

COPY user_tile_updates (id, tile_id, zoom_level, "timestamp", query, x_label, y_label, z_label, x_inv, y_inv, z_inv, color, width, height, user_id, dataset_id) FROM stdin;
\.


--
-- Name: user_tile_updates_id_seq; Type: SEQUENCE SET; Schema: public; Owner: testuser
--

SELECT pg_catalog.setval('user_tile_updates_id_seq', 1, false);


--
-- Data for Name: user_traces; Type: TABLE DATA; Schema: public; Owner: testuser
--

COPY user_traces (id, tile_id, zoom_level, "timestamp", query, user_id, dataset_id) FROM stdin;
\.


--
-- Name: user_traces_id_seq; Type: SEQUENCE SET; Schema: public; Owner: testuser
--

SELECT pg_catalog.setval('user_traces_id_seq', 1, false);


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: testuser
--

COPY users (id, flask_session_id, done) FROM stdin;
\.


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: testuser
--

SELECT pg_catalog.setval('users_id_seq', 1, true);


--
-- Name: data_sets_name_key; Type: CONSTRAINT; Schema: public; Owner: testuser; Tablespace: 
--

ALTER TABLE ONLY data_sets
    ADD CONSTRAINT data_sets_name_key UNIQUE (name);


--
-- Name: data_sets_pkey; Type: CONSTRAINT; Schema: public; Owner: testuser; Tablespace: 
--

ALTER TABLE ONLY data_sets
    ADD CONSTRAINT data_sets_pkey PRIMARY KEY (id);


--
-- Name: data_sets_query_key; Type: CONSTRAINT; Schema: public; Owner: testuser; Tablespace: 
--

ALTER TABLE ONLY data_sets
    ADD CONSTRAINT data_sets_query_key UNIQUE (query);


--
-- Name: survey_questions_pkey; Type: CONSTRAINT; Schema: public; Owner: testuser; Tablespace: 
--

ALTER TABLE ONLY survey_questions
    ADD CONSTRAINT survey_questions_pkey PRIMARY KEY (id);


--
-- Name: survey_responses_pkey; Type: CONSTRAINT; Schema: public; Owner: testuser; Tablespace: 
--

ALTER TABLE ONLY survey_responses
    ADD CONSTRAINT survey_responses_pkey PRIMARY KEY (id);


--
-- Name: surveys_pkey; Type: CONSTRAINT; Schema: public; Owner: testuser; Tablespace: 
--

ALTER TABLE ONLY surveys
    ADD CONSTRAINT surveys_pkey PRIMARY KEY (id);


--
-- Name: uix_1; Type: CONSTRAINT; Schema: public; Owner: testuser; Tablespace: 
--

ALTER TABLE ONLY survey_questions
    ADD CONSTRAINT uix_1 UNIQUE (survey_id, question_text);


--
-- Name: uix_2; Type: CONSTRAINT; Schema: public; Owner: testuser; Tablespace: 
--

ALTER TABLE ONLY survey_responses
    ADD CONSTRAINT uix_2 UNIQUE (question_id, value);


--
-- Name: uix_3; Type: CONSTRAINT; Schema: public; Owner: testuser; Tablespace: 
--

ALTER TABLE ONLY user_tile_selections
    ADD CONSTRAINT uix_3 UNIQUE (tile_id, zoom_level, query, user_id);


--
-- Name: user_responses_pkey; Type: CONSTRAINT; Schema: public; Owner: testuser; Tablespace: 
--

ALTER TABLE ONLY user_responses
    ADD CONSTRAINT user_responses_pkey PRIMARY KEY (id);


--
-- Name: user_tile_selections_pkey; Type: CONSTRAINT; Schema: public; Owner: testuser; Tablespace: 
--

ALTER TABLE ONLY user_tile_selections
    ADD CONSTRAINT user_tile_selections_pkey PRIMARY KEY (id);


--
-- Name: user_tile_updates_pkey; Type: CONSTRAINT; Schema: public; Owner: testuser; Tablespace: 
--

ALTER TABLE ONLY user_tile_updates
    ADD CONSTRAINT user_tile_updates_pkey PRIMARY KEY (id);


--
-- Name: user_traces_pkey; Type: CONSTRAINT; Schema: public; Owner: testuser; Tablespace: 
--

ALTER TABLE ONLY user_traces
    ADD CONSTRAINT user_traces_pkey PRIMARY KEY (id);


--
-- Name: users_flask_session_id_key; Type: CONSTRAINT; Schema: public; Owner: testuser; Tablespace: 
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_flask_session_id_key UNIQUE (flask_session_id);


--
-- Name: users_pkey; Type: CONSTRAINT; Schema: public; Owner: testuser; Tablespace: 
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: survey_questions_survey_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: testuser
--

ALTER TABLE ONLY survey_questions
    ADD CONSTRAINT survey_questions_survey_id_fkey FOREIGN KEY (survey_id) REFERENCES surveys(id);


--
-- Name: survey_responses_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: testuser
--

ALTER TABLE ONLY survey_responses
    ADD CONSTRAINT survey_responses_question_id_fkey FOREIGN KEY (question_id) REFERENCES survey_questions(id);


--
-- Name: user_responses_question_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: testuser
--

ALTER TABLE ONLY user_responses
    ADD CONSTRAINT user_responses_question_id_fkey FOREIGN KEY (question_id) REFERENCES survey_questions(id);


--
-- Name: user_responses_response_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: testuser
--

ALTER TABLE ONLY user_responses
    ADD CONSTRAINT user_responses_response_id_fkey FOREIGN KEY (response_id) REFERENCES survey_responses(id);


--
-- Name: user_responses_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: testuser
--

ALTER TABLE ONLY user_responses
    ADD CONSTRAINT user_responses_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);


--
-- Name: user_tile_selections_dataset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: testuser
--

ALTER TABLE ONLY user_tile_selections
    ADD CONSTRAINT user_tile_selections_dataset_id_fkey FOREIGN KEY (dataset_id) REFERENCES data_sets(id);


--
-- Name: user_tile_selections_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: testuser
--

ALTER TABLE ONLY user_tile_selections
    ADD CONSTRAINT user_tile_selections_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);


--
-- Name: user_tile_updates_dataset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: testuser
--

ALTER TABLE ONLY user_tile_updates
    ADD CONSTRAINT user_tile_updates_dataset_id_fkey FOREIGN KEY (dataset_id) REFERENCES data_sets(id);


--
-- Name: user_tile_updates_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: testuser
--

ALTER TABLE ONLY user_tile_updates
    ADD CONSTRAINT user_tile_updates_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);


--
-- Name: user_traces_dataset_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: testuser
--

ALTER TABLE ONLY user_traces
    ADD CONSTRAINT user_traces_dataset_id_fkey FOREIGN KEY (dataset_id) REFERENCES data_sets(id);


--
-- Name: user_traces_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: testuser
--

ALTER TABLE ONLY user_traces
    ADD CONSTRAINT user_traces_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

