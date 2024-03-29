# Experimentation

I attended a talk in college once where the lecturer stated
that most computer scientists tend to do more engineering than science,
as many of our processes are not data driven nor follow the scientific method. It was a great lecture, and I was reminded of it when I began
doing A/B tests professionally. They are a scientific way to 
test new features, and provide helpful features that make engineering
those features easier, such as:

- Allows for gradual percent rollout of new features, significantly limiting the impact of buggy and bad features.
- Programmatic access to the experiment allows for the feature/experiment
  to be rolled back independent of the application, nearly instantly
- Programmatic access to the experiment also allows for it to so lay
  dormant in the application until kicked off
- Easy, quantified results of a new feature's impact

This implements experimentation through sessions, both so that participants are
put into experiments in a mostly "masked" trial, as they are not associated with a long lived cookie
or a application data model like User (although that is an option, and some experiments will only make sense to be run for logged in users), and to avoid cookie privacy and hacking concerns.

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
a new variant. Optionally, you can also override the variant you see using `?r_v_b_override=<variant_name>`. We can explore removing these test/admin users from the experiment entirely, but having large enough participants that the experiment to reach significance would
likely mean these users become insignificant.


The variants are:

- red_no_text
- red_with_text
- blue_no_text
- blue_with_text
- control (default)

This experiment has 4 variations and a control, so it may take some time to
reach statistical significance, compared to one with less. It also has
a lot of covariance between models, which I am sure a real statistician
could use to decrease that time, but that is out of scope at the moment.

Screenshots of what each look like:
- [red_no_text](./screenshots/button_alt_red_no_text.png)
- [red_with_text](./screenshots/button_alt_red_with_text.png)
- [blue_no_text](./screenshots/button_alt_blue_no_text.png)
- [blue_with_text](./screenshots/button_alt_blue_with_text.png)
- [control (default)](./screenshots/button_alt_control.png)

[Experiment summary](./screenshots/experiment_summary.png)


## Test Application

The test application contains a simple `User` model, please don't put important passwords in it.

## Testing
1. `export ENV_STAGE=testing`
2. `make test`
