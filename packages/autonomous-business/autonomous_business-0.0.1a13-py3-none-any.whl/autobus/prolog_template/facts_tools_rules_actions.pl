:- use_module(library(prosqlite)).

% Optional: still allow running as a script
:- initialization(main).

% -----------------------------
% Public entry point
% -----------------------------

%% main/0
%% Entry point to run the program
main :-
    init_db,
    save_outcome_to_database,
    sqlite_disconnect(db).

% -----------------------------
% Database initialization 
% -----------------------------

db_path('database/db.sqlite').
outcome_table('people_with_age').

init_db :-
    db_path(DbPath),
    sqlite_connect(DbPath, db,
                   [ exists(true),
                     as_predicates(true),
                     arity(arity)
                   ]).

% -----------------------------
% Table-as-predicate
% -----------------------------

% After sqlite_connect/3 with as_predicates(true),
% the table `people` and `output_table` becomes the predicates:
%
%   people(Id, Name)
%   output_table(Id, Name) 

% -----------------------------
% Call tools via Python function
% -----------------------------

%% person_age(+Name, -Age)
%% Calls Python age_of(Name) -> Age
person_age(Name, Age) :-
    % Janus expects Python function name as an atom; it looks it up in __main__
    py_call('auto_bus.demo.tool_simulation':call_web_search_agent(Name), Age).

% -----------------------------
% Business rules
% -----------------------------



% -----------------------------
% Actions
% -----------------------------
%% save_outcome_to_database/0
%% Clears output_table then copies every row from people into output_table.
save_outcome_to_database :-
    % remove existing rows from output table
    outcome_table(OutcomeTable),
    format(atom(DeleteSql), "DELETE FROM ~w;", [OutcomeTable]),
    sqlite_query(db, DeleteSql, _),

    % iterate rows and insert them into output_table
    forall( people(Id, Name),
            (
                person_age(Name, Age),
                escape_sql_string(Name, Escaped),
                % build a safe SQL literal for the name (single-quoted, with single quotes doubled)
                outcome_table(OutcomeTable),
                format(atom(SQL), "INSERT INTO ~w VALUES (~w, '~w', ~w);", [OutcomeTable, Id, Escaped, Age]),
                sqlite_query(db, SQL, _)
            )
          ).

% -----------------------------
% Helpers
% -----------------------------

%% escape_sql_string(+In:string, -Out:atom)
%% Replace single quotes ' with '' for safe SQL single-quoted literal insertion.
escape_sql_string(In, Out) :-
    % split on single quote
    split_string(In, "'", "'", Parts),
    % join with doubled single-quote
    atomic_list_concat(Parts, "''", Out).

% -----------------------------
% End of file
% -----------------------------
