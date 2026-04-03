import traceback
from lerobot.async_inference.helpers import prepare_raw_observation, PolicyFeature, FeatureType

robot_obs = {'left_front': [1,2,3], 'left_env': [1], 'right_front': [1]}
lerobot_features = {
    'observation.images.left_front': {'dtype': 'image'},
    'observation.images.left_env': {'dtype': 'image'},
    'observation.images.right_front': {'dtype': 'image'},
    'observation.state': {'dtype': 'float32', 'shape': [1], 'names': ['a']}
}
policy_image_features = {
    'observation.images.camera1': PolicyFeature(type=FeatureType.VISUAL, shape=(3,224,224)),
    'observation.images.camera2': PolicyFeature(type=FeatureType.VISUAL, shape=(3,224,224)),
    'observation.images.camera3': PolicyFeature(type=FeatureType.VISUAL, shape=(3,224,224))
}
rename_map = {
    "observation.images.left_env": "observation.images.camera1", 
    "observation.images.left_front": "observation.images.camera2", 
    "observation.images.right_front": "observation.images.camera3"
}

try:
    prepare_raw_observation(robot_obs, lerobot_features, policy_image_features, rename_map)
except Exception as e:
    traceback.print_exc()
