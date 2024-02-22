# Experimentation

I attended a talk in college once where the lecturer stated
that most computer scientists tend to do more engineering than science,
as many of our processes are not data driven nor follow the scientific method. Tabs vs spaces, 


## Quickstart
Setup environment variables of interest:

Either:
    `MONGO_USER` and `MONGO_PASSWORD` and `MONGO_DEPLOYMENT_SUBDOMAIN`
  or
    `MONGO_DB_URI`

- ENV_STAGE (optional=dev)
- FLASK_SECRET_KEY (really anything)
- BUTTON_EXPERIMENT_UUID (optional, see Test Experimetn section for more)

1. `make install-requirements`
2. `make test-server`

See the Makefile for more commands.

## Test Experiment

A sample experiment can be created with `src.services.Helpful.build_button_experiment`, where you can also provide the number of
test participants to start with. This will return a dictionary
that contains the experiment and variants as model objects, and the
participant UUIDs. You can then set the environment variable `BUTTON_EXPERIMENT_UUID` to begin to see users allocated to the experiment.

The concept of a participant is the same as the session_uuid generated,
meaning that you will need to eaither logout or open a new browser to see
a new variant. Optionally, you can also override the variant you see using `?r_v_b_override=<variant_name>`. We will have to explore removing these test/admin users from the experiment entirely, but having large enough participants that the experiment to reach significance would
likely mean these users become insignificant.


The variants are:

- red_no_text
- red_with_text
- blue_no_text
- blue_with_text
- control (default)


## Test Application

The test application contains a simple `User` model, please don't put important passwords in it.

## Testing
1. `export ENV_STAGE=testing`
2. `make test`

### Nice features:
- Enable/disable experiments `ExperimentService`
- Enable/disable experiments with environment variables
- Variable number of variants
