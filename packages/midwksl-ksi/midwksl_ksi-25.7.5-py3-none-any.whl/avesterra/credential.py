""" 
Copyright (c) [Midwest Knowledge System Labs & Plex - Alexander Larkin] [2025-2026]
Copyright (c) [LEDR Technologies Inc.] [2024-2025]
This file is part of the Orchestra library, which helps developer use our Orchestra technology which is based on AvesTerra, owned and developed by Georgetown University, under license agreement with LEDR Technologies Inc.
The Orchestra library is a free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
The Orchestra library is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.
You should have received a copy of the GNU Lesser General Public License along with the Orchestra library. If not, see <https://www.gnu.org/licenses/>.
If you have any questions, feedback or issues about the Orchestra library, you can contact us at support@midwksl.net.
"""



import avesterra.features as features
import avesterra.tokens as tokens
from avesterra.avesterra import AvEntity, AvMask, AvAuthorization
from avesterra.avial import AvKey, entity_key, AvValue, NULL_ENTITY
from avesterra.compartments import compartment_valid
from avesterra.identities import identity_valid
import avesterra.facts as facts
from avesterra.taxonomy import AvAttribute
import avesterra.compartments as compartments
import avesterra.identities as identities





def issue_credential(
    compartment: AvEntity,
    identity: AvEntity,
    mask: AvMask,
    authorization: AvAuthorization,
):
    """
    Issues a credential to an identity within a compartment with specified permissions.

    A credential is essentially a compartment token with permissions (AVESTERRA, READ,
    WRITE, EXECUTE, DELETE) that enables seamless multi-compartment access without
    manual token switching. The credential creates a mapping between the identity's
    authority and the compartment's authority, allowing the identity's token to
    automatically resolve to the appropriate compartment credential based on the
    target entity's authority during operations.

    Args:
        compartment (AvEntity): Target compartment entity for credential issuance.
        identity (AvEntity): Identity entity receiving the credential.
        mask (AvMask): Permission mask defining access levels (AVESTERRA, READ,
                      WRITE, EXECUTE, DELETE) for the credential.
        authorization (AvAuthorization): Authorization with sufficient privileges
                                       to issue credentials in the compartment.

    Raises:
        ValueError: When compartment or identity is invalid for credential issuance.
        AuthorizationError: When authorization lacks credential issuance privileges.
        EntityError: When credential mapping fails due to system constraints.

    Example:
        >>> research_comp = lookup_compartment("research-key", admin_auth)
        >>> alex_identity = lookup_identity("alex-key", admin_auth)
        >>> read_write_mask = AvMask.READ | AvMask.WRITE
        >>> issue_credential(
        ...     research_comp,
        ...     alex_identity,
        ...     read_write_mask,
        ...     admin_auth
        ... )
    """

    compartment_key: AvKey = entity_key(entity=compartment, authorization=authorization)
    identity_key: AvKey = entity_key(entity=identity, authorization=authorization)

    if compartment_valid(
        compartment=compartment, authorization=authorization
    ) and identity_valid(identity=identity, authorization=authorization):
        facts.include_fact(
            entity=compartment,
            attribute=AvAttribute.CREDENTIAL,
            authorization=authorization,
        )

        compartment_authority: AvAuthorization = compartments.compartment_authority(
            compartment=compartment, authorization=authorization
        )
        identity_authority: AvAuthorization = identities.identity_authority(
            identity=identity, authorization=authorization
        )

        features.include_feature(
            entity=compartment,
            attribute=AvAttribute.CREDENTIAL,
            name=f"{mask}",
            key=identity_key,
            value=AvValue.encode_entity(identity),
            authorization=authorization,
        )
        features.include_feature(
            entity=identity,
            attribute=AvAttribute.CREDENTIAL,
            name=f"{mask}",
            key=compartment_key,
            value=AvValue.encode_entity(compartment),
            authorization=authorization,
        )
        tokens.map(
            server=NULL_ENTITY,
            token=identity_authority,
            mask=mask,
            authority=compartment_authority,
            authorization=authorization,
        )
    else:
        if not compartment_valid(compartment=compartment, authorization=authorization):
            raise ValueError(
                f"Invalid compartment {compartment} given for credential issuance"
            )
        if not identity_valid(identity=identity, authorization=authorization):
            raise ValueError(
                f"Invalid identity {identity} given for credential issuance"
            )


def retract_credential(
    compartment: AvEntity, identity: AvEntity, authorization: AvAuthorization
):
    """
    Retracts a credential from an identity within a compartment.

    Removes the credential relationship between an identity and compartment,
    eliminating the automatic token-to-compartment-authority mapping.

    Args:
        compartment (AvEntity): Compartment entity to retract credential from.
        identity (AvEntity): Identity entity losing the credential.
        authorization (AvAuthorization): Authorization with sufficient privileges
                                       to retract credentials from the compartment.

    Raises:
        ValueError: When compartment or identity is invalid for credential retraction.
        AuthorizationError: When authorization lacks credential retraction privileges.
        EntityError: When credential unmapping fails due to system constraints.

    Example:
        >>> retract_credential(research_comp, former_user, admin_auth)
    """

    compartment_key: AvKey = entity_key(entity=compartment, authorization=authorization)
    identity_key: AvKey = entity_key(entity=identity, authorization=authorization)

    if compartment_valid(
        compartment=compartment, authorization=authorization
    ) and identity_valid(identity=identity, authorization=authorization):
        facts.include_fact(
            entity=compartment,
            attribute=AvAttribute.CREDENTIAL,
            authorization=authorization,
        )

        compartment_authority: AvAuthorization = compartments.compartment_authority(
            compartment=compartment, authorization=authorization
        )
        identity_authority: AvAuthorization = identities.identity_authority(
            identity=identity, authorization=authorization
        )

        features.exclude_feature(
            entity=compartment,
            attribute=AvAttribute.CREDENTIAL,
            key=identity_key,
            authorization=authorization,
        )
        features.exclude_feature(
            entity=identity,
            attribute=AvAttribute.CREDENTIAL,
            key=compartment_key,
            authorization=authorization,
        )
        tokens.unmap(
            server=NULL_ENTITY,
            token=identity_authority,
            authority=compartment_authority,
            authorization=authorization,
        )
    else:
        if not compartment_valid(compartment=compartment, authorization=authorization):
            raise ValueError(
                f"Invalid compartment {compartment} given for credential retraction"
            )
        if not identity_valid(identity=identity, authorization=authorization):
            raise ValueError(
                f"Invalid identity {identity} given for credential retraction"
            )
