use std::sync::Arc;

use tokio_test::assert_ready;
use tower_test::mock::Spawn;

use crate::{
    crypto::{ByteObject, PublicEncryptKey},
    mask::Model,
    services::{
        fetchers::{
            MaskLengthRequest,
            MaskLengthService,
            ModelRequest,
            ModelService,
            RoundParamsRequest,
            RoundParamsService,
            ScalarRequest,
            ScalarService,
        },
        tests::utils::new_event_channels,
    },
    state_machine::{
        coordinator::{RoundParameters, RoundSeed},
        events::{MaskLengthUpdate, ModelUpdate, ScalarUpdate},
    },
};

#[tokio::test]
async fn test_mask_length_svc() {
    let (mut publisher, subscriber) = new_event_channels();

    let mut task = Spawn::new(MaskLengthService::new(&subscriber));
    assert_ready!(task.poll_ready()).unwrap();

    let resp = task.call(MaskLengthRequest).await;
    assert_eq!(resp, Ok(None));

    let round_id = subscriber.params_listener().get_latest().round_id;
    publisher.broadcast_mask_length(round_id.clone(), MaskLengthUpdate::New(42));
    assert_ready!(task.poll_ready()).unwrap();
    let resp = task.call(MaskLengthRequest).await;
    assert_eq!(resp, Ok(Some(42)));

    publisher.broadcast_mask_length(round_id, MaskLengthUpdate::Invalidate);
    assert_ready!(task.poll_ready()).unwrap();
    let resp = task.call(MaskLengthRequest).await;
    assert_eq!(resp, Ok(None));
}

#[tokio::test]
async fn test_model_svc() {
    let (mut publisher, subscriber) = new_event_channels();

    let mut task = Spawn::new(ModelService::new(&subscriber));
    assert_ready!(task.poll_ready()).unwrap();

    let resp = task.call(ModelRequest).await;
    assert_eq!(resp, Ok(None));

    let round_id = subscriber.params_listener().get_latest().round_id;
    let model = Arc::new(Model::from(vec![]));
    publisher.broadcast_model(round_id.clone(), ModelUpdate::New(model.clone()));
    assert_ready!(task.poll_ready()).unwrap();
    let resp = task.call(ModelRequest).await;
    assert_eq!(resp, Ok(Some(model)));

    publisher.broadcast_model(round_id, ModelUpdate::Invalidate);
    assert_ready!(task.poll_ready()).unwrap();
    let resp = task.call(ModelRequest).await;
    assert_eq!(resp, Ok(None));
}

#[tokio::test]
async fn test_round_params_svc() {
    let (mut publisher, subscriber) = new_event_channels();
    let initial_params = subscriber.params_listener().get_latest().event;

    let mut task = Spawn::new(RoundParamsService::new(&subscriber));
    assert_ready!(task.poll_ready()).unwrap();

    let resp = task.call(RoundParamsRequest).await;
    assert_eq!(resp, Ok(initial_params));

    let params = RoundParameters {
        pk: PublicEncryptKey::fill_with(0x11),
        sum: 0.42,
        update: 0.42,
        seed: RoundSeed::fill_with(0x11),
    };
    publisher.broadcast_params(params.clone());
    assert_ready!(task.poll_ready()).unwrap();
    let resp = task.call(RoundParamsRequest).await;
    assert_eq!(resp, Ok(params));
}

#[tokio::test]
async fn test_scalar_svc() {
    let (mut publisher, subscriber) = new_event_channels();

    let mut task = Spawn::new(ScalarService::new(&subscriber));
    assert_ready!(task.poll_ready()).unwrap();

    let resp = task.call(ScalarRequest).await;
    assert_eq!(resp, Ok(None));

    let round_id = subscriber.params_listener().get_latest().round_id;
    publisher.broadcast_scalar(round_id.clone(), ScalarUpdate::New(42.42));
    assert_ready!(task.poll_ready()).unwrap();
    let resp = task.call(ScalarRequest).await;
    assert_eq!(resp, Ok(Some(42.42)));

    publisher.broadcast_scalar(round_id, ScalarUpdate::Invalidate);
    assert_ready!(task.poll_ready()).unwrap();
    let resp = task.call(ScalarRequest).await;
    assert_eq!(resp, Ok(None));
}
