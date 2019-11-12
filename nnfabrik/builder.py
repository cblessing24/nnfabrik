from . import utility
from . import datasets
from . import training
from . import models
from functools import partial

from .utility.nnf_helper import split_module_name, dynamic_import


def get_model(model_fn, model_config, dataloader, seed=None, state_dict=None, strict=True):
    """
    Resolves `model_fn` and invokes the resolved function with `model_config` keyword arguments as well as the `dataloader` and `seed`.
    Note that the resolved `model_fn` is expected to accept the `dataloader` as the first positional argument and `seed` as a keyword argument.
    If you pass in `state_dict`, the resulting nn.Module instance will be loaded with the state_dict, using appropriate `strict` mode for loading.

    Args:
        model_fn: string name of the model builder function path to be resolved. Alternatively, you can pass in a callable object and no name resolution will be performed.
        model_config: a dictionary containing keyword arguments to be passed into the resolved `model_fn`
        dataloader: (a dictionary of) dataloaders to be passed into the resolved `model_fn` as the first positional argument
        seed: randomization seed to be passed in to as a keyword argument into the resolved `model_fn`
        state_dict: If provided, the resulting nn.Module object will be loaded with the state_dict before being returned
        strict: Controls the `strict` mode of nn.Module.load_state_dict

    Returns:
        Resulting nn.Module object.
    """

    if isinstance(model_fn, str):
        module_path, class_name = split_module_name(model_fn)
        model_fn = dynamic_import(module_path, class_name) if module_path else eval('models.' + model_fn)

    net = model_fn(dataloader, seed=seed, **model_config)

    if state_dict is not None:
        net.load_state_dict(state_dict, strict=strict)

    return net


def get_data(dataset_fn, dataset_config):
    """
    Resolves `dataset_fn` and invokes the resolved function onto the `dataset_config` configuration dictionary. The resulting
    dataloader will be returned.

    Args:
        dataset_fn: string name of the dataloader function path to be resolved. Alternatively, you can pass in a callable object and no name resolution will be performed.
        dataset_config: a dictionary containing keyword arguments to be passed into the resolved `dataset_fn`

    Returns:
        Result of invoking the resolved `dataset_fn` with `dataset_config` as keyword arguments.
    """
    if isinstance(dataset_fn, str):
        module_path, class_name = split_module_name(dataset_fn)
        dataset_fn = dynamic_import(module_path, class_name) if module_path else eval('datasets.' + dataset_fn)

    return dataset_fn(**dataset_config)


def get_trainer(trainer_fn, trainer_config=None):
    """
    If `trainer_fn` string is passed, resolves and returns the corresponding function. If `trainer_config` is passed in,
    a partial function is created with the configuration object expanded.

    Args:
        trainer_fn: string name of the function path to be resolved. Alternatively, you can pass in a callable object and no name resolution will be performed.
        trainer_config: If passed in, a partial function will be creating expanding `trainer_config` as the keyword arguments into the resolved trainer_fn

    Returns:
        Resolved trainer function
    """
    print(trainer_config)
    
    if isinstance(trainer_fn, str):
        module_path, class_name = split_module_name(trainer_fn)
        trainer_fn = dynamic_import(module_path, class_name) if module_path else eval('training.' + trainer_fn)
        return trainer_fn(**trainer_config)
    
    if trainer_config is not None:
        trainer_fn = partial(trainer_fn, **trainer_config)
        return trainer_fn


def get_all_parts(dataset_fn, dataset_config, model_fn, model_config, seed=None, dl_key='train', state_dict=None, strict=True, trainer_fn=None, trainer_config=None):
    dataloaders = get_data(dataset_fn, dataset_config)

    model = get_model(model_fn, model_config, dataloaders[dl_key], seed=seed, state_dict=state_dict, strict=strict)

    if trainer_fn is not None:
        trainer = get_trainer(trainer_fn, trainer_config)
        return dataloaders, model, trainer
    else:
        return dataloaders, model

