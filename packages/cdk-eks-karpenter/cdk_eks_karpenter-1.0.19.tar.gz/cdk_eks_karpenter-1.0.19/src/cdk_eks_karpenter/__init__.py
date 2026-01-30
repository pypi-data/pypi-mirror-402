r'''
# cdk-eks-karpenter

This construct configures the necessary dependencies and installs [Karpenter](https://karpenter.sh)
on an EKS cluster managed by AWS CDK.

## Prerequisites

### Usage with EC2 Spot Capacity

If you have not used EC2 spot in your AWS account before, follow the instructions
[here](https://karpenter.sh/v0.31/getting-started/getting-started-with-karpenter/#3-create-a-cluster) to create
the service linked role in your account allowing Karpenter to provision EC2 Spot Capacity.

## Using

In your CDK project, initialize a new Karpenter construct for your EKS cluster, like this:

```python
const cluster = new Cluster(this, 'testCluster', {
  vpc: vpc,
  role: clusterRole,
  version: KubernetesVersion.V1_27,
  defaultCapacity: 1
});

const karpenter = new Karpenter(this, 'Karpenter', {
  cluster: cluster,
  namespace: "kube-system"
});
```

This will install and configure Karpenter in your cluster. To have Karpenter do something useful, you
also need to create an [EC2NodeClass](https://karpenter.sh/docs/concepts/nodeclasses/) and an
[NodePool](https://karpenter.sh/docs/concepts/nodepools/), for a more complete example, see
[test/integ.karpenter.ts](./test/integ.karpenter.ts).

## Known issues

### It is now a best practice to install Karpenter into the kube-system namespace:

Kapenter CRD webhooks have 'kube-system' hard-coded into them, and do not work in other namespaces (such as 'karpenter')

### Versions earlier than v0.6.1 fails to install

As of [aws/karpenter#1145](https://github.com/aws/karpenter/pull/1145) the Karpenter Helm chart is
refactored to specify `clusterEndpoint` and `clusterName` on the root level of the chart values, previously
these values was specified under the key `controller`.

## Testing

This construct adds a custom task to [projen](https://projen.io/), so you can test a full deployment
of an EKS cluster with Karpenter installed as specified in `test/integ.karpenter.ts` by running the
following:

```sh
export CDK_DEFAULT_REGION=<aws region>
export CDK_DEFAULT_ACCOUNT=<account id>
npx projen test:deploy
```

As the above will create a cluster without EC2 capacity, with CoreDNS and Karpenter running as Fargate
pods, you can test out the functionality of Karpenter by deploying an inflation deployment, which will
spin up a number of pods that will trigger Karpenter creation of worker nodes:

```sh
kubectl apply -f test/inflater-deployment.yml
```

You can clean things up by deleting the deployment and the CDK test stack:

```sh
kubectl delete -f test/inflater-deployment.yml
npx projen test:destroy
```

## FAQ

### I'm not able to launch spot instances

1. Ensure you have the appropriate linked role available in your account, for more details,
   see [the karpenter documentation](https://karpenter.sh/v0.31/getting-started/getting-started-with-karpenter/#3-create-a-cluster)
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

import aws_cdk.aws_eks as _aws_cdk_aws_eks_ceddda9d
import aws_cdk.aws_iam as _aws_cdk_aws_iam_ceddda9d
import constructs as _constructs_77d1e7e8


class Karpenter(
    _constructs_77d1e7e8.Construct,
    metaclass=jsii.JSIIMeta,
    jsii_type="cdk-eks-karpenter.Karpenter",
):
    def __init__(
        self,
        scope: _constructs_77d1e7e8.Construct,
        id: builtins.str,
        *,
        cluster: _aws_cdk_aws_eks_ceddda9d.Cluster,
        version: builtins.str,
        helm_extra_values: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
        namespace: typing.Optional[builtins.str] = None,
        node_role: typing.Optional[_aws_cdk_aws_iam_ceddda9d.Role] = None,
        service_account_name: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param scope: -
        :param id: -
        :param cluster: The EKS Cluster to attach to.
        :param version: The helm chart version to install. Default: - latest
        :param helm_extra_values: Extra values to pass to the Karpenter Helm chart.
        :param namespace: The Kubernetes namespace to install to. Default: karpenter
        :param node_role: Custom NodeRole to pass for Karpenter Nodes.
        :param service_account_name: The Kubernetes ServiceAccount name to use. Default: karpenter
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__469ebeca9f5de13870f679bde48f92e084c84974eb076da23d6515dcec4c3ed9)
            check_type(argname="argument scope", value=scope, expected_type=type_hints["scope"])
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
        props = KarpenterProps(
            cluster=cluster,
            version=version,
            helm_extra_values=helm_extra_values,
            namespace=namespace,
            node_role=node_role,
            service_account_name=service_account_name,
        )

        jsii.create(self.__class__, self, [scope, id, props])

    @jsii.member(jsii_name="addEC2NodeClass")
    def add_ec2_node_class(
        self,
        id: builtins.str,
        ec2_node_class_spec: typing.Mapping[builtins.str, typing.Any],
    ) -> typing.Mapping[builtins.str, typing.Any]:
        '''addEC2NodeClass adds a EC2NodeClass to the Karpenter configuration.

        :param id: must consist of lower case alphanumeric characters, '-' or '.', and must start and end with an alphanumeric character.
        :param ec2_node_class_spec: spec of Karpenters EC2NodeClass API.

        :return: the metadata object of the created manifest
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__47ce8790d2e75f38ffe737d41870a352f050c300240e299a50f1096f471591a7)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument ec2_node_class_spec", value=ec2_node_class_spec, expected_type=type_hints["ec2_node_class_spec"])
        return typing.cast(typing.Mapping[builtins.str, typing.Any], jsii.invoke(self, "addEC2NodeClass", [id, ec2_node_class_spec]))

    @jsii.member(jsii_name="addManagedPolicyToKarpenterRole")
    def add_managed_policy_to_karpenter_role(
        self,
        managed_policy: _aws_cdk_aws_iam_ceddda9d.IManagedPolicy,
    ) -> None:
        '''addManagedPolicyToKarpenterRole adds Managed Policies To Karpenter Role.

        :param managed_policy: - iam managed policy to add to the karpenter role.
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__7c0fa5f4f02bfe7dcd3e1618714e7cb5a527b8fd6ba783719a452d6af22c4ae2)
            check_type(argname="argument managed_policy", value=managed_policy, expected_type=type_hints["managed_policy"])
        return typing.cast(None, jsii.invoke(self, "addManagedPolicyToKarpenterRole", [managed_policy]))

    @jsii.member(jsii_name="addNodePool")
    def add_node_pool(
        self,
        id: builtins.str,
        node_pool_spec: typing.Mapping[builtins.str, typing.Any],
    ) -> typing.Mapping[builtins.str, typing.Any]:
        '''addNodePool adds a NodePool to the Karpenter configuration.

        :param id: must consist of lower case alphanumeric characters, '-' or '.', and must start and end with an alphanumeric character.
        :param node_pool_spec: spec of Karpenters NodePool API.

        :return: the metadata object of the created manifest
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__6f5b58a7ccec1afdb470ed862dbf14fee15a3d2b9ad9cb5c07bfd81bff709317)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument node_pool_spec", value=node_pool_spec, expected_type=type_hints["node_pool_spec"])
        return typing.cast(typing.Mapping[builtins.str, typing.Any], jsii.invoke(self, "addNodePool", [id, node_pool_spec]))

    @jsii.member(jsii_name="addNodeTemplate")
    def add_node_template(
        self,
        id: builtins.str,
        node_template_spec: typing.Mapping[builtins.str, typing.Any],
    ) -> None:
        '''(deprecated) addNodeTemplate adds a node template manifest to the cluster.

        Currently the node template spec
        parameter is relatively free form.

        :param id: - must consist of lower case alphanumeric characters, '-' or '.', and must start and end with an alphanumeric character.
        :param node_template_spec: - spec of Karpenters Node Template object.

        :deprecated: This method should not be used with Karpenter >v0.32.0

        :stability: deprecated
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__3554e9a499a68bf31650e3a7390ddcd8c655a2d2adbbe5b710b9fcf2a8132fd2)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument node_template_spec", value=node_template_spec, expected_type=type_hints["node_template_spec"])
        return typing.cast(None, jsii.invoke(self, "addNodeTemplate", [id, node_template_spec]))

    @jsii.member(jsii_name="addProvisioner")
    def add_provisioner(
        self,
        id: builtins.str,
        provisioner_spec: typing.Mapping[builtins.str, typing.Any],
    ) -> None:
        '''(deprecated) addProvisioner adds a provisioner manifest to the cluster.

        Currently the provisioner spec
        parameter is relatively free form.

        :param id: - must consist of lower case alphanumeric characters, '-' or '.', and must start and end with an alphanumeric character.
        :param provisioner_spec: - spec of Karpenters Provisioner object.

        :deprecated: This method should not be used with Karpenter >v0.32.0

        :stability: deprecated
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__f10a5511016d6e74144c7f6b09b4924cb5d9184ea7db898f95fb85a4ad63c95c)
            check_type(argname="argument id", value=id, expected_type=type_hints["id"])
            check_type(argname="argument provisioner_spec", value=provisioner_spec, expected_type=type_hints["provisioner_spec"])
        return typing.cast(None, jsii.invoke(self, "addProvisioner", [id, provisioner_spec]))

    @builtins.property
    @jsii.member(jsii_name="cluster")
    def cluster(self) -> _aws_cdk_aws_eks_ceddda9d.Cluster:
        return typing.cast(_aws_cdk_aws_eks_ceddda9d.Cluster, jsii.get(self, "cluster"))

    @builtins.property
    @jsii.member(jsii_name="helmExtraValues")
    def helm_extra_values(self) -> typing.Any:
        return typing.cast(typing.Any, jsii.get(self, "helmExtraValues"))

    @builtins.property
    @jsii.member(jsii_name="namespace")
    def namespace(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "namespace"))

    @builtins.property
    @jsii.member(jsii_name="nodeRole")
    def node_role(self) -> _aws_cdk_aws_iam_ceddda9d.Role:
        return typing.cast(_aws_cdk_aws_iam_ceddda9d.Role, jsii.get(self, "nodeRole"))

    @builtins.property
    @jsii.member(jsii_name="serviceAccountName")
    def service_account_name(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "serviceAccountName"))

    @builtins.property
    @jsii.member(jsii_name="version")
    def version(self) -> builtins.str:
        return typing.cast(builtins.str, jsii.get(self, "version"))

    @builtins.property
    @jsii.member(jsii_name="helmChartValues")
    def helm_chart_values(self) -> typing.Mapping[builtins.str, typing.Any]:
        return typing.cast(typing.Mapping[builtins.str, typing.Any], jsii.get(self, "helmChartValues"))

    @helm_chart_values.setter
    def helm_chart_values(
        self,
        value: typing.Mapping[builtins.str, typing.Any],
    ) -> None:
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__1e206ee251711a10854759f8d11ccd42fb723fb0550d8e49f1ff830d7c2ffc9b)
            check_type(argname="argument value", value=value, expected_type=type_hints["value"])
        jsii.set(self, "helmChartValues", value) # pyright: ignore[reportArgumentType]


@jsii.data_type(
    jsii_type="cdk-eks-karpenter.KarpenterProps",
    jsii_struct_bases=[],
    name_mapping={
        "cluster": "cluster",
        "version": "version",
        "helm_extra_values": "helmExtraValues",
        "namespace": "namespace",
        "node_role": "nodeRole",
        "service_account_name": "serviceAccountName",
    },
)
class KarpenterProps:
    def __init__(
        self,
        *,
        cluster: _aws_cdk_aws_eks_ceddda9d.Cluster,
        version: builtins.str,
        helm_extra_values: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
        namespace: typing.Optional[builtins.str] = None,
        node_role: typing.Optional[_aws_cdk_aws_iam_ceddda9d.Role] = None,
        service_account_name: typing.Optional[builtins.str] = None,
    ) -> None:
        '''
        :param cluster: The EKS Cluster to attach to.
        :param version: The helm chart version to install. Default: - latest
        :param helm_extra_values: Extra values to pass to the Karpenter Helm chart.
        :param namespace: The Kubernetes namespace to install to. Default: karpenter
        :param node_role: Custom NodeRole to pass for Karpenter Nodes.
        :param service_account_name: The Kubernetes ServiceAccount name to use. Default: karpenter
        '''
        if __debug__:
            type_hints = typing.get_type_hints(_typecheckingstub__4559ecf2c12f8389d9503c7bff63c0e1d38df33a2f13e5dac618bececf369e7d)
            check_type(argname="argument cluster", value=cluster, expected_type=type_hints["cluster"])
            check_type(argname="argument version", value=version, expected_type=type_hints["version"])
            check_type(argname="argument helm_extra_values", value=helm_extra_values, expected_type=type_hints["helm_extra_values"])
            check_type(argname="argument namespace", value=namespace, expected_type=type_hints["namespace"])
            check_type(argname="argument node_role", value=node_role, expected_type=type_hints["node_role"])
            check_type(argname="argument service_account_name", value=service_account_name, expected_type=type_hints["service_account_name"])
        self._values: typing.Dict[builtins.str, typing.Any] = {
            "cluster": cluster,
            "version": version,
        }
        if helm_extra_values is not None:
            self._values["helm_extra_values"] = helm_extra_values
        if namespace is not None:
            self._values["namespace"] = namespace
        if node_role is not None:
            self._values["node_role"] = node_role
        if service_account_name is not None:
            self._values["service_account_name"] = service_account_name

    @builtins.property
    def cluster(self) -> _aws_cdk_aws_eks_ceddda9d.Cluster:
        '''The EKS Cluster to attach to.'''
        result = self._values.get("cluster")
        assert result is not None, "Required property 'cluster' is missing"
        return typing.cast(_aws_cdk_aws_eks_ceddda9d.Cluster, result)

    @builtins.property
    def version(self) -> builtins.str:
        '''The helm chart version to install.

        :default: - latest
        '''
        result = self._values.get("version")
        assert result is not None, "Required property 'version' is missing"
        return typing.cast(builtins.str, result)

    @builtins.property
    def helm_extra_values(
        self,
    ) -> typing.Optional[typing.Mapping[builtins.str, typing.Any]]:
        '''Extra values to pass to the Karpenter Helm chart.'''
        result = self._values.get("helm_extra_values")
        return typing.cast(typing.Optional[typing.Mapping[builtins.str, typing.Any]], result)

    @builtins.property
    def namespace(self) -> typing.Optional[builtins.str]:
        '''The Kubernetes namespace to install to.

        :default: karpenter
        '''
        result = self._values.get("namespace")
        return typing.cast(typing.Optional[builtins.str], result)

    @builtins.property
    def node_role(self) -> typing.Optional[_aws_cdk_aws_iam_ceddda9d.Role]:
        '''Custom NodeRole to pass for Karpenter Nodes.'''
        result = self._values.get("node_role")
        return typing.cast(typing.Optional[_aws_cdk_aws_iam_ceddda9d.Role], result)

    @builtins.property
    def service_account_name(self) -> typing.Optional[builtins.str]:
        '''The Kubernetes ServiceAccount name to use.

        :default: karpenter
        '''
        result = self._values.get("service_account_name")
        return typing.cast(typing.Optional[builtins.str], result)

    def __eq__(self, rhs: typing.Any) -> builtins.bool:
        return isinstance(rhs, self.__class__) and rhs._values == self._values

    def __ne__(self, rhs: typing.Any) -> builtins.bool:
        return not (rhs == self)

    def __repr__(self) -> str:
        return "KarpenterProps(%s)" % ", ".join(
            k + "=" + repr(v) for k, v in self._values.items()
        )


__all__ = [
    "Karpenter",
    "KarpenterProps",
]

publication.publish()

def _typecheckingstub__469ebeca9f5de13870f679bde48f92e084c84974eb076da23d6515dcec4c3ed9(
    scope: _constructs_77d1e7e8.Construct,
    id: builtins.str,
    *,
    cluster: _aws_cdk_aws_eks_ceddda9d.Cluster,
    version: builtins.str,
    helm_extra_values: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
    namespace: typing.Optional[builtins.str] = None,
    node_role: typing.Optional[_aws_cdk_aws_iam_ceddda9d.Role] = None,
    service_account_name: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__47ce8790d2e75f38ffe737d41870a352f050c300240e299a50f1096f471591a7(
    id: builtins.str,
    ec2_node_class_spec: typing.Mapping[builtins.str, typing.Any],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__7c0fa5f4f02bfe7dcd3e1618714e7cb5a527b8fd6ba783719a452d6af22c4ae2(
    managed_policy: _aws_cdk_aws_iam_ceddda9d.IManagedPolicy,
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__6f5b58a7ccec1afdb470ed862dbf14fee15a3d2b9ad9cb5c07bfd81bff709317(
    id: builtins.str,
    node_pool_spec: typing.Mapping[builtins.str, typing.Any],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__3554e9a499a68bf31650e3a7390ddcd8c655a2d2adbbe5b710b9fcf2a8132fd2(
    id: builtins.str,
    node_template_spec: typing.Mapping[builtins.str, typing.Any],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__f10a5511016d6e74144c7f6b09b4924cb5d9184ea7db898f95fb85a4ad63c95c(
    id: builtins.str,
    provisioner_spec: typing.Mapping[builtins.str, typing.Any],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__1e206ee251711a10854759f8d11ccd42fb723fb0550d8e49f1ff830d7c2ffc9b(
    value: typing.Mapping[builtins.str, typing.Any],
) -> None:
    """Type checking stubs"""
    pass

def _typecheckingstub__4559ecf2c12f8389d9503c7bff63c0e1d38df33a2f13e5dac618bececf369e7d(
    *,
    cluster: _aws_cdk_aws_eks_ceddda9d.Cluster,
    version: builtins.str,
    helm_extra_values: typing.Optional[typing.Mapping[builtins.str, typing.Any]] = None,
    namespace: typing.Optional[builtins.str] = None,
    node_role: typing.Optional[_aws_cdk_aws_iam_ceddda9d.Role] = None,
    service_account_name: typing.Optional[builtins.str] = None,
) -> None:
    """Type checking stubs"""
    pass
