import sys
from pathlib import Path
from importlib import import_module
from multiprocessing import Process

from ..plot import (
    seg_max_fig,
    spike_image,
)
from .common import (
    finish,
    print_stats,
    set_env,
)


def call(name, *args, **kwargs):
    def wrap(cfg, *args, **kwargs):
        set_env(cfg)
        return target(cfg, *args, **kwargs)

    target = getattr(import_module(f"hotaru.cui.{name}"), name)
    p = Process(target=wrap, args=args, kwargs=kwargs)
    p.start()
    p.join()
    if p.exitcode != 0:
        sys.exit()


def run(cfg):
    for stage in range(cfg.max_train_step + 1):
        if stage == 0:
            call("normalize", cfg)
            call("init", cfg)
        else:
            call("spatial", cfg, stage)
        call("temporal", cfg, stage)

        print_stats(cfg, stage)
        if finish(cfg, stage):
            break

    path = Path(cfg.outputs.figs.dir)
    path.mkdir(parents=True, exist_ok=True)
    seg_max_fig(cfg, stage).write_image(path / "run_footprints.pdf")
    spike_image(cfg, stage)[0].save(path / "run_spike.pdf")
