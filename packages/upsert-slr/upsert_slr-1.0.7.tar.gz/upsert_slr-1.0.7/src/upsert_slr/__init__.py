r'''
# Upsert Service-Linked Role

AWS CDK construct to create a [service-linked role (SLR)](https://docs.aws.amazon.com/IAM/latest/UserGuide/using-service-linked-roles.html) if there is no SLR for the same service, and if there is, skip the creation process.

![architecture](imgs/architecture.png)

## Features

* Create a service-linked role. If it is already created in the same AWS account, just skip the creation.
* Standalone CFn template since no CDK assets are used. We use inline code for the Lambda function.
* Sleep some time after role creation to wait for IAM propagation.

## Usage

```sh
npm install upsert-slr
```

```python
import { ServiceLinkedRole } from 'upsert-slr';

new ServiceLinkedRole(this, 'ElasticsearchSlr', {
    awsServiceName: 'es.amazonaws.com',
    description: 'Service linked role for Elasticsearch',
});
```

## Why do we need this?

CloudFormation also supports a service-linked role ([doc](https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/aws-resource-iam-servicelinkedrole.html)). Why do we need this?

Because the resource behaves strangely when there is already a role with the same name. All we need is to simply create a role, and skip it if it already exists. Such behavior as upsert is achieved by this construct, `upsert-slr`.

Also, even if CFn successfully creates a role, resources that depend on the role sometimes fail to be created because there is sometimes a delay before the role is actually available. See [this stack overflow](https://stackoverflow.com/questions/20156043/how-long-should-i-wait-after-applying-an-aws-iam-policy-before-it-is-valid) for more details.

To avoid the IAM propagation delay, this construct also waits for some time after a role is created.
'''
from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)

import abc
import builtins
import datetime
import enum
import typing

import jsii
import publication
import typing_extensions

import typeguard
from importlib.metadata import version as _metadata_package_version
TYPEGUARD_MAJOR_VERSION = int(_metadata_package_version('typeguard').split('.')[0])

def check_type(argname: str, value: object, expected_type: typing.Any) -> typing.Any:
    if TYPEGUARD_MAJOR_VERSION <= 2:
        return typeguard.check_type(argname=argname, value=value, expected_type=expected_type) # type:ignore
    else:
        if isinstance(value, jsii._reference_map.InterfaceDynamicProxy): # pyright: ignore [reportAttributeAccessIssue]
           pass
        else:
            if TYPEGUARD_MAJOR_VERSION == 3:
                typeguard.config.collection_check_strategy = typeguard.CollectionCheckStrategy.ALL_ITEMS # type:ignore
                typeguard.check_type(value=value, expected_type=expected_type) # type:ignore
            else:
                typeguard.check_type(value=value, expected_type=expected_type, collection_check_strategy=typeguard.CollectionCheckStrategy.ALL_ITEMS) # type:ignore

from ._jsii import *

import constructs as _constructs_77d1e7e8


class ServiceLinkedRole(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="upsert-slr.ServiceLinkedRole",
):
    def __init__(
        self,
        scope: "_constructs_77d1e7e8.Construct",
        id: builtins.str,
        *,
        aws_service_name: builtins.str,
        description: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param aws_service_name: The service principal for the AWS service to which this role is attached. You use a string similar to a URL but without the http:// in front. For example: elasticbeanstalk.amazonaws.com . Service principals are unique and case-sensitive. To find the exact service principal for your service-linked role, see AWS services that work with IAM in the IAM User Guide. Look for the services that have Yes in the Service-Linked Role column. Choose the Yes link to view the service-linked role documentation for that service. https://docs.aws.amazon.com/IAM/latest/UserGuide/using-service-linked-roles.html
        :param description: The description of the role. This is only used when creating a new role. When there is an existing role for the aws service, this field is ignored. Default: no description
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__eaefcb6bfa6686267d9fbe8ed893ee66abd33592269a0f87588ddf3ea490fc74)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = ServiceLinkedRoleProps(
            aws_service_name=aws_service_name, description=description
        )

        jsii.create(self.__class__, self, [scope, id, props])


@jsii.data_type(
    jsii_type="upsert-slr.ServiceLinkedRoleProps",
    jsii_struct_bases=[],
    name_mapping={"aws_service_name": "awsServiceName", "description": "description"},
)
class ServiceLinkedRoleProps:
    def __init__(
        self,
        *,
        aws_service_name: builtins.str,
        description: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param aws_service_name: The service principal for the AWS service to which this role is attached. You use a string similar to a URL but without the http:// in front. For example: elasticbeanstalk.amazonaws.com . Service principals are unique and case-sensitive. To find the exact service principal for your service-linked role, see AWS services that work with IAM in the IAM User Guide. Look for the services that have Yes in the Service-Linked Role column. Choose the Yes link to view the service-linked role documentation for that service. https://docs.aws.amazon.com/IAM/latest/UserGuide/using-service-linked-roles.html
        :param description: The description of the role. This is only used when creating a new role. When there is an existing role for the aws service, this field is ignored. Default: no description
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__2b465f6bb28878e03ea2345c60b3a08d2ec8243a9fd855266499358ddd9a2940)
            check_type(argname="argument aws_service_name", value=aws_service_name, expected_type=type_hints["aws_service_name"])
            check_type(argname="argument description", value=description, expected_type=type_hints["description"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "aws_service_name": aws_service_name,
        }
        if description is not None:
            self._values["description"] = description

    @builtins.property
    def aws_service_name(self) -> builtins.str:
        '''The service principal for the AWS service to which this role is attached.

        You use a string similar to a URL but without the http:// in front. For example: elasticbeanstalk.amazonaws.com .

        Service principals are unique and case-sensitive. To find the exact service principal for your service-linked role, see AWS services that work with IAM in the IAM User Guide. Look for the services that have Yes in the Service-Linked Role column. Choose the Yes link to view the service-linked role documentation for that service.
        https://docs.aws.amazon.com/IAM/latest/UserGuide/using-service-linked-roles.html
        '''
        result = self._values.get("aws_service_name")
        assert result is not None, "Required property 'aws_service_name' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def description(self) -> typing.Optional[builtins.str]:
        '''The description of the role.

        This is only used when creating a new role.
        When there is an existing role for the aws service, this field is ignored.

        :default: no description
        '''
        result = self._values.get("description")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "ServiceLinkedRoleProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "ServiceLinkedRole",
    "ServiceLinkedRoleProps",
]

publication.publish()

def _typecheckingstub__eaefcb6bfa6686267d9fbe8ed893ee66abd33592269a0f87588ddf3ea490fc74(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    aws_service_name: builtins.str,
    description: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__2b465f6bb28878e03ea2345c60b3a08d2ec8243a9fd855266499358ddd9a2940(
    *,
    aws_service_name: builtins.str,
    description: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass
