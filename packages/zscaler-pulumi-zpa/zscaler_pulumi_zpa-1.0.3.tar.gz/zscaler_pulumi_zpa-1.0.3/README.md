# ZPA Resource Provider

[![NPM Version](https://badge.fury.io/js/@bdzscaler%2Fpulumi-zpa.svg)](https://badge.fury.io/js/@bdzscaler%2Fpulumi-zpa)
[![Python Version](https://badge.fury.io/py/zscaler-pulumi-zpa.svg)](https://pypi.org/project/zscaler-pulumi-zpa/)
[![NuGet version](https://badge.fury.io/nu/Zscaler.Zpa.svg)](https://badge.fury.io/nu/Zscaler.Zpa)
[![PkgGoDev](https://pkg.go.dev/badge/github.com/pulumi/pulumi-pulumiservice/sdk/go/pulumiservice)](https://pkg.go.dev/github.com/zscaler/pulumi-zpa/sdk/go/zpa)
[![Zscaler Community](https://img.shields.io/badge/zscaler-community-blue)](https://community.zscaler.com/)

## Support Disclaimer

-> **Disclaimer:** Please refer to our [General Support Statement](docs/guides/support.md) before proceeding with the use of this provider. You can also refer to our [troubleshooting guide](docs/guides/troubleshooting.md) for guidance on typical problems.


The ZPA Resource Provider for Pulumi lets you manage [ZPA](http://github.com/zscaler/pulumi-zpa) resources. To use
this package, please [install the Pulumi CLI first](https://pulumi.com/).

## Installing

This package is available for several languages/platforms:

### Node.js (JavaScript/TypeScript)

To use from JavaScript or TypeScript in Node.js, install using either `npm`:

```bash
npm install @bdzscaler/pulumi-zpa
```

or `yarn`:

```bash
yarn add @bdzscaler/pulumi-zpa
```

### Python

To use from Python, install using `pip`:

```bash
pip install zscaler-pulumi-zpa
```

### Go

To use from Go, use `go get` to grab the latest version of the library:

```bash
go get github.com/zscaler/pulumi-zpa/sdk/go/...
```

### .NET

To use from .NET, install using `dotnet add package`:

```bash
dotnet add package Zscaler.Zpa
```

## Configuration

The following configuration points are available for the `zpa` provider:

- `zpa:client_id` (client id: `ZPA_CLIENT_ID`) - the client id for `zpa`
- `zpa:client_secret` (client secret: `ZPA_CLIENT_SECRET`) - the client secret for `zpa`
- `zpa:customer_id` (customer id: `ZPA_CUSTOMER_ID`) - the customer id that identifies the ZPA tenant
- `zpa:cloud` (cloud environment: `ZPA_CLOUD`) - the cloud environment in which to deploy resources

## Reference

For detailed reference documentation, please visit [the Pulumi registry](https://www.pulumi.com/registry/packages/zpa/api-docs/).

## Support

This template/solution are released under an as-is, best effort, support
policy. These scripts should be seen as community supported and Zscaler
Business Development Team will contribute our expertise as and when possible.
We do not provide technical support or help in using or troubleshooting the components
of the project through our normal support options such as Zscaler support teams,
or ASC (Authorized Support Centers) partners and backline
support options. The underlying product used (Zscaler Internet Access API) by the
scripts or templates are still supported, but the support is only for the
product functionality and not for help in deploying or using the template or
script itself. Unless explicitly tagged, all projects or work posted in our
GitHub repository at (<https://github.com/zscaler>) or sites other
than our official Downloads page on <https://support.zscaler.com>
are provided under the best effort policy.
