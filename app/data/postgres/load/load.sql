\set userstudyapploadroot '/home/leilani/webapps/user_study/'
\set userstudyapploadpath 'app/data/postgres/load/'
\set userstudyappdatasetsfile 'data_sets.txt'
\set userstudyappsurveysfile 'surveys.txt'
\set userstudyappquestionsfile 'questions.txt'
\set userstudyappresponsesfile 'responses.txt'
\set userstudyapploaddatasets '\'':userstudyapploadroot:userstudyapploadpath:userstudyappdatasetsfile'\''
\set userstudyapploadsurveys '\'':userstudyapploadroot:userstudyapploadpath:userstudyappsurveysfile'\''
\set userstudyapploadquestions '\'':userstudyapploadroot:userstudyapploadpath:userstudyappquestionsfile'\''
\set userstudyapploadresponses '\'':userstudyapploadroot:userstudyapploadpath:userstudyappresponsesfile'\''

copy data_sets from :userstudyapploaddatasets csv header;
copy surveys from :userstudyapploadsurveys csv header;
copy survey_questions from :userstudyapploadquestions csv header;
copy survey_responses from :userstudyapploadresponses csv header;
