"""
This pipeline serves as example of a custom (simple) pipeline created from scratch.

More elaborated pipelines are provided as python modules, usually published in PyPi.
See the py-youwol documentation https://l.youwol.com/doc/py-youwol
"""

from typing import List
from youwol.environment import YouwolEnvironment
from youwol.environment.models_project import Artifact, Flow, Pipeline, PipelineStep, FileListing, IPipelineFactory
from youwol.pipelines.pipeline_typescript_weback_npm import PublishCdnLocalStep, \
    create_sub_pipelines_publish
from youwol.routers.projects import JsBundle
from youwol_utils.context import Context
from youwol_utils.utils_paths import parse_json

index_html = "index.html"
package_json = "package.json"
style_css = "style.css"

all_files = [index_html, package_json, style_css]


class InitStep(PipelineStep):
    id: str = "init"
    run: str = "npm install"
    sources: FileListing = FileListing(
        include=[package_json]
    )


class BuildStep(PipelineStep):
    id: str = "build"
    run: str = "npm run build"
    sources: FileListing = FileListing(
        include=[package_json, "src/**"]
    )

    artifacts: List[Artifact] = [
        Artifact(
            id='build',
            files=FileListing(
                include=[package_json, "build"]
            )
        )
    ]


class PipelineFactory(IPipelineFactory):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def get(self, _env: YouwolEnvironment, ctx: Context):

        publish_remote_steps, dags = await create_sub_pipelines_publish(start_step="cdn-local", context=ctx)

        return Pipeline(
            target=JsBundle(
                links=[]
            ),
            tags=["javascript", "library", "npm"],
            projectName=lambda path: parse_json(path / package_json)["name"],
            projectVersion=lambda path: parse_json(path / package_json)["version"],
            steps=[
                      InitStep(),
                      BuildStep(),
                      PublishCdnLocalStep(packagedArtifacts=['build']),
                  ] + publish_remote_steps,
            flows=[
                Flow(
                    name="prod",
                    dag=[
                            "init > build > cdn-local",
                        ] + dags
                )
            ]
        )
