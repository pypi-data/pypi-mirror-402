""" 
Copyright (c) [Midwest Knowledge System Labs & Plex - Alexander Larkin] [2025-2026]
Copyright (c) [LEDR Technologies Inc.] [2024-2025]
This file is part of the Orchestra library, which helps developer use our Orchestra technology which is based on AvesTerra, owned and developed by Georgetown University, under license agreement with LEDR Technologies Inc.
The Orchestra library is a free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
The Orchestra library is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.
You should have received a copy of the GNU Lesser General Public License along with the Orchestra library. If not, see <https://www.gnu.org/licenses/>.
If you have any questions, feedback or issues about the Orchestra library, you can contact us at support@midwksl.net.
"""
from avesterra import connect_outlet

from avesterra.outlets import delete_outlet
from avesterra.avial import *
from avesterra.predefined import access_outlet
import avesterra.facts as facts
import avesterra.identities as identities
import avesterra.tokens as tokens
import avesterra.features as features


AvCompartment = AvEntity


def create_compartment(name: str, key: str, authorization: AvAuthorization) -> AvEntity:
    """
    Creates a new compartment in the AvesTerra distributed graph database.
    
    A compartment serves as a security boundary similar to a group on computer systems.
    The compartment has its own Token and Authority, enabling identities to operate
    with compartment privileges when granted access. The created compartment enables
    token-based authorization switching for granted identities.
    
    Args:
        name (str): Human-readable name identifier for the compartment, stored in 
                   the entity's Name metadata field.
        key (str): Key identifier for compartment lookups, stored in the entity's 
                  Key metadata field.
        authorization (AvAuthorization): Authorization that is able to perform operation.
    
    Returns:
        AvEntity: The newly created compartment with unique EUID.
    
    Raises:
        AvesTerraError: When compartment with the same key already exists.
        AuthorizationError: When authorization lacks creation privileges.
        EntityError: When compartment creation fails due to system constraints.
    
    Example:
        >>> admin_auth = AvAuthorization.simple("admin-token")
        >>> research_comp = create_compartment(
        ...     "Research Division", 
        ...     "research-key", 
        ...     admin_auth
        ... )
        >>> print(research_comp)
        <0|0|123456>
    """
    if not features.feature_member(
        entity=access_outlet,
        attribute=AvAttribute.COMPARTMENT,
        key=key,
        authorization=authorization,
    ):
        token: AvAuthorization = AvAuthorization.random()
        authority: AvAuthorization = AvAuthorization.random()

        # Create compartment that is attached to compartment adapter
        compartment_entity: AvEntity = create_entity(
            name=name,
            key=key,
            context=AvContext.AVESTERRA,
            category=AvCategory.AVESTERRA,
            klass=AvClass.COMPARTMENT,
            outlet=access_outlet,
            authorization=authorization,
        )

        # Connect compartment to compartment adapter
        connect_outlet(
            entity=compartment_entity,
            outlet=access_outlet,
            authorization=authorization,
        )

        # Invoke create compartment method on compartment adapter
        invoke_entity(
            entity=compartment_entity,
            method=AvMethod.CREATE,
            authorization=authorization,
        )

        # Reference compartment so that it doesn't vanish on server reboot
        reference_entity(entity=compartment_entity, authorization=authorization)

        # Create compartment "outlet"
        comp_outlet: AvEntity = create_entity(
            name=name,
            key=key,
            context=AvContext.AVESTERRA,
            category=AvCategory.AVESTERRA,
            klass=AvClass.AVESTERRA,
            outlet=access_outlet,
            authorization=authorization,
        )
        activate_entity(outlet=comp_outlet, authorization=authorization)

        # Change authority of entity to `authority`
        change_entity(
            entity=comp_outlet, authority=authority, authorization=authorization
        )

        # Reference compartment outlet, so it doesn't get rebooted
        # into oblivion
        reference_entity(entity=comp_outlet, authorization=authorization)

        # Setup compartment fields on compartment
        facts.set_fact(
            entity=compartment_entity,
            attribute=AvAttribute.OUTLET,
            value=AvValue.encode(comp_outlet),
            authorization=authorization,
        )

        facts.set_fact(
            entity=compartment_entity,
            attribute=AvAttribute.TOKEN,
            value=AvValue.encode_string(str(token)),
            authorization=authorization,
        )

        facts.set_fact(
            entity=compartment_entity,
            attribute=AvAttribute.AUTHORITY,
            value=AvValue.encode_string(str(authority)),
            authorization=authorization,
        )

        facts.set_fact(
            entity=compartment_entity,
            attribute=AvAttribute.IDENTITY,
            value=NULL_VALUE,
            authorization=authorization,
        )

        features.set_feature(
            entity=access_outlet,
            attribute=AvAttribute.COMPARTMENT,
            name=name,
            key=str(key),
            value=AvValue.encode(compartment_entity),
            authorization=authorization,
        )

        features.set_feature(
            entity=access_outlet,
            attribute=AvAttribute.KEY,
            name=name,
            key=str(token),
            value=AvValue.encode_string(key),
            authorization=authorization,
        )

        # Allow authority of compartment to invoke
        # on the NULL_ENTITY(Place where tokens are stored)
        authorize_entity(
            entity=NULL_ENTITY,
            restrictions=FALSE_PARAMETER,
            authority=authority,
            authorization=authorization,
        )

        # Enable token -> authority mapping in AvesTerra
        tokens.instate(
            server=NULL_ENTITY,
            token=token,
            authority=authority,
            authorization=authorization,
        )

        return compartment_entity
    else:
        raise AvesTerraError("Compartment already exists")


def delete_compartment(compartment: AvEntity, authorization: AvAuthorization):
    """
    Permanently deletes a compartment from the AvesTerra system.

    Removes the compartment and cleans up all of its associated tokens and authority.

    Args:
        compartment (AvEntity): Valid compartment to delete.
        authorization (AvAuthorization): Authorization that is able to perform operation.
    
    Raises:
        AuthorizationError: When compartment is invalid or authorization lacks 
                           deletion privileges.
        EntityError: When compartment deletion fails.
    
    Example:
        >>> delete_compartment(old_compartment, admin_auth)
    """

    comp_key: AvKey = entity_key(entity=compartment, authorization=authorization)
    if compartment_valid(compartment=compartment, authorization=authorization):
        # Get compartment authority
        authority: AvAuthorization = compartment_authority(
            compartment=compartment, authorization=authorization
        )

        # Get compartment outlet
        comp_outlet: AvEntity = facts.fact_value(
            entity=compartment,
            attribute=AvAttribute.OUTLET,
            authorization=authorization,
        ).decode_entity()

        # De-authorize compartment auth from accessing NULL_ENTITY(token -> authority mapping)
        deauthorize_entity(
            entity=NULL_ENTITY, authority=authority, authorization=authorization
        )

        # Dereference compartment outlet
        dereference_entity(entity=comp_outlet, authorization=authorization)

        # Delete compartment outlet
        delete_outlet(outlet=comp_outlet, authorization=authorization)

        # Remove identitys from compartment
        while (
                features.feature_count(
                entity=compartment,
                attribute=AvAttribute.IDENTITY,
                authorization=authorization,
            )
                != 0
        ):
            # Get identity key from compartment identity feature
            identity_key: str = features.feature_key(
                entity=compartment,
                attribute=AvAttribute.IDENTITY,
                authorization=authorization,
            )

            # Get identity from identity key
            identity: AvEntity = identities.lookup_identity(
                key=identity_key, authorization=authorization
            )

            # Revoke compartment access from identity
            revoke_compartment(
                compartment=compartment, identity=identity, authorization=authorization
            )

        # Remove compartment from compartment
        # adapter outlet
        features.exclude_feature(
            entity=access_outlet,
            attribute=AvAttribute.COMPARTMENT,
            key=comp_key,
            authorization=authorization,
        )

        # Dereference compartment to enable deletion
        dereference_entity(entity=compartment, authorization=authorization)

        # Delete compartment from AvesTerra
        delete_entity(entity=compartment, authorization=authorization)
    else:
        raise AuthorizationError("invalid compartment")


def grant_compartment(
    compartment: AvEntity, identity: AvEntity, authorization: AvAuthorization
):
    """
    Grants compartment access to an identity, enabling token switching.
    
    The identity can then exchange their token for the compartment token to operate with compartment
    authority privileges; may not work with all function calls, but will for most.
    
    Args:
        compartment (AvEntity): Target compartment for access grant.
        identity (AvEntity): Identity entity receiving compartment access.
        authorization (AvAuthorization): Authorization that is able to perform operation.
    
    Raises:
        AuthorizationError: When compartment or identity is invalid, or 
                           authorization lacks modification privileges.
        EntityError: When entities are improperly configured.
    
    Example:
        >>> grant_compartment(
        ...     research_comp, 
        ...     user_identity, 
        ...     admin_auth
        ... )
    """

    comp_key: str = entity_key(entity=compartment, authorization=authorization)

    identity_key: str = entity_key(entity=identity, authorization=authorization)

    if compartment_valid(
        compartment=compartment, authorization=authorization
    ) and identities.identity_valid(identity=identity, authorization=authorization):
        if not features.feature_member(
            entity=compartment,
            attribute=AvAttribute.IDENTITY,
            key=identity_key,
            authorization=authorization,
        ):
            # Generate compartment token for identity
            new_token = AvAuthorization.random()

            # Get compartment authority
            comp_authority: AvAuthorization = compartment_authority(
                compartment=compartment, authorization=authorization
            )

            # Get compartment outlet
            comp_outlet: AvEntity = compartment_outlet(
                compartment=compartment, authorization=authorization
            )

            # Get identity authority
            ident_authority: AvAuthorization = identities.identity_authority(
                identity=identity, authorization=authorization
            )

            # Get identity outlet
            ident_outlet: AvEntity = identities.identity_outlet(
                identity=identity, authorization=authorization
            )

            features.set_feature(
                entity=compartment,
                attribute=AvAttribute.IDENTITY,
                key=identity_key,
                value=AvValue.encode(identity),
                authorization=authorization,
            )

            features.set_feature(
                entity=compartment,
                attribute=AvAttribute.AUTHORIZATION,
                key=identity_key,
                value=AvValue.encode_string(str(new_token)),
                authorization=authorization,
            )

            features.set_feature(
                entity=identity,
                attribute=AvAttribute.COMPARTMENT,
                key=comp_key,
                value=AvValue.encode(compartment),
                authorization=authorization,
            )

            # Allow the compartment authority
            # to access the identity outlet
            authorize_entity(
                entity=ident_outlet,
                authority=comp_authority,
                authorization=ident_authority,
            )

            # Subscribe identity outlet to the compartment outlet
            subscribe_event(
                entity=comp_outlet, outlet=ident_outlet, authorization=authorization
            )

            # Allow the newly generated compartment token
            # for the identity to map to the compartment
            # authority
            tokens.instate(
                server=NULL_ENTITY,
                token=new_token,
                authority=comp_authority,
                authorization=authorization,
            )
    else:
        if not compartment_valid(compartment=compartment, authorization=authorization):
            raise AuthorizationError("invalid compartment/identity")


def revoke_compartment(
    compartment: AvEntity, identity: AvEntity, authorization: AvAuthorization
):
    """
    Revokes compartment access from an identity.
    
    The identity loses the ability to exchange their token for the compartment token.
    
    Args:
        compartment (AvEntity): compartment to revoke access from.
        identity (AvEntity): Identity entity losing compartment access.
        authorization (AvAuthorization): Authorization that is able to perform operation.
    
    Raises:
        AuthorizationError: When compartment/identity is invalid or authorization 
                           lacks modification privileges.
    
    Example:
        >>> revoke_compartment(research_comp, former_user, admin_auth)
    """
    comp_key: str = entity_key(entity=compartment, authorization=authorization)
    identity_key: str = entity_key(entity=identity, authorization=authorization)

    if compartment_valid(
        compartment=compartment, authorization=authorization
    ) and features.feature_member(
        entity=compartment,
        attribute=AvAttribute.IDENTITY,
        key=identity_key,
        authorization=authorization,
    ):
        token: AvAuthorization = AvAuthorization(
            features.feature_value(
                entity=compartment,
                attribute=AvAttribute.AUTHORIZATION,
                key=identity_key,
                authorization=authorization,
            ).decode_string()
        )

        tokens.destate(server=NULL_ENTITY, token=token, authorization=authorization)

        comp_authority: AvAuthorization = compartment_authority(
            compartment=compartment, authorization=authorization
        )
        comp_outlet: AvEntity = compartment_outlet(
            compartment=compartment, authorization=authorization
        )

        ident_authority: AvAuthorization = identities.identity_authority(
            identity=identity, authorization=authorization
        )
        ident_outlet: AvEntity = identities.identity_outlet(
            identity=identity, authorization=authorization
        )

        # Remove compartment access to identity
        deauthorize_entity(
            entity=ident_outlet, authority=comp_authority, authorization=ident_authority
        )

        try:
            unsubscribe_event(
                entity=comp_outlet, outlet=ident_outlet, authorization=authorization
            )
        except Exception:
            pass

        # Remove person from compartment
        features.exclude_feature(
            entity=compartment,
            attribute=AvAttribute.IDENTITY,
            key=identity_key,
            authorization=authorization,
        )
        features.exclude_feature(
            entity=compartment,
            attribute=AvAttribute.AUTHORIZATION,
            key=identity_key,
            authorization=authorization,
        )

        # Remove identity from compartment
        features.exclude_feature(
            entity=identity,
            attribute=AvAttribute.COMPARTMENT,
            key=comp_key,
            authorization=authorization,
        )
        return

    raise AuthorizationError("invalid compartment/identity")


def enable_privilege(
    compartment: AvEntity, identity: AvEntity, authorization: AvAuthorization
):
    """
    Enables privileged access for an identity within a compartment.
    
    Grants the identity direct access to the compartment's Authority when
    they exchange tokens. This allows the identity to use all AvesTerra
    calls that require Authority passing, such as Adapt and Wait operations.
    WARNING: Use with extreme caution as this grants equivalent powers to
    the compartment itself.
    
    Args:
        compartment (AvEntity): Target compartment.
        identity (AvEntity): Identity entity receiving privileged access.
        authorization (AvAuthorization): Authorization that is able to perform operation.
    
    Example:
        >>> enable_privilege(research_comp, trusted_admin, super_auth)
    """

    identity_key: str = entity_key(entity=identity, authorization=authorization)

    features.set_feature(
        entity=compartment,
        attribute=AvAttribute.PRIVILEGE,
        key=identity_key,
        value=AvValue.encode(identity),
        authorization=authorization,
    )


def disable_privilege(
    compartment: AvEntity, identity: AvEntity, authorization: AvAuthorization
):
    """
    Disables privileged access for an identity within a compartment.
    
    Removes the identity's direct access to compartment Authority, restricting
    them to standard compartment token operations. The identity retains basic
    compartment access but loses Authority-level privileges.
    
    Args:
        compartment (AvEntity): Target compartment.
        identity (AvEntity): Identity entity losing privileged access.
        authorization (AvAuthorization): Authorization that is able to perform operation.
    
    Example:
        >>> disable_privilege(research_comp, former_admin, super_auth)
    """
    identity_key: str = entity_key(entity=identity, authorization=authorization)

    features.exclude_feature(
        entity=compartment,
        attribute=AvAttribute.PRIVILEGE,
        key=identity_key,
        authorization=authorization,
    )


def compartment_authority(
    compartment: AvEntity, authorization: AvAuthorization
) -> AvAuthorization:
    """
    Retrieves the Authority for a compartment.
    
    Returns the 128-bit Authority that has complete control
    over the compartment. This Authority can modify the compartment's
    authorization list and perform any operation within the compartment
    scope.
    
    Args:
        compartment (AvEntity): compartment to query for authority.
        authorization (AvAuthorization): Authorization that is able to perform operation.
    
    Returns:
        AvAuthorization: The Authority authorization for the compartment.
    
    Raises:
        AuthorizationError: When compartment is invalid or authorization lacks
                           authority access privileges.
    
    Example:
        >>> authority = compartment_authority(research_comp, view_auth)
        >>> print(f"Compartment authority: {authority}")
    """
    if compartment_valid(compartment=compartment, authorization=authorization):
        return AvAuthorization(
            facts.fact_value(
                entity=compartment,
                attribute=AvAttribute.AUTHORITY,
                authorization=authorization,
            ).decode_string()
        )
    else:
        raise AuthorizationError("Invalid compartment")


def authenticated_authority(
    comp_key: AvKey, identity_key: AvKey, ident_token: AvAuthorization
) -> AvAuthorization:
    """
    
    Returns the compartment-specific authority available to an authenticated identity.
    
    Args:
        comp_key (AvKey): Key identifier for the target compartment.
        identity_key (AvKey): Key identifier for the identity.
        ident_token (AvAuthorization): Identity's authentication token.
    
    Returns:
        AvAuthorization: The authority authorization for authenticated operations.
    
    Example:
        >>> auth = authenticated_authority("research-key", "user-key", token)
    """
    return AvAuthorization(
        invoke_entity(
            entity=access_outlet,
            method=AvMethod.GET,
            attribute=AvAttribute.AUTHORITY,
            name=comp_key,
            key=identity_key,
            value=AvValue.encode_string(str(ident_token)),
            authorization=VERIFY_AUTHORIZATION,
        ).decode_string()
    )


def compartment_key(token: AvAuthorization):
    """
    Retrieves the compartment key identifier from a compartment token.
    
    Resolves a compartment token back to its associated compartment key,
    enabling reverse lookup operations for token-based compartment
    identification.
    
    Args:
        token (AvAuthorization): Compartment token for key lookup.
    
    Returns:
        The key identifier associated with the compartment token.
    
    Example:
        >>> key = compartment_key(comp_token)
        >>> print(f"Token maps to key: {key}")
    """
    return invoke_entity(
        entity=access_outlet,
        method=AvMethod.GET,
        attribute=AvAttribute.KEY,
        name=NULL_NAME,
        key=str(token),
        authorization=VERIFY_AUTHORIZATION,
    ).decode()


def compartment_token(
    compartment: AvEntity,
    authorization: AvAuthorization,
):
    """
    Returns the compartment's token
    
    Args:
        compartment (AvEntity): compartment to query for token.
        authorization (AvAuthorization): Authorization that is able to perform operation.
    
    Returns:
        AvAuthorization: The base compartment token.
    
    Raises:
        AuthorizationError: When compartment is invalid or authorization lacks
                           token access privileges.
    
    Example:
        >>> token = compartment_token(research_comp, admin_auth)
    """
    if compartment_valid(compartment=compartment, authorization=authorization):
        return AvAuthorization(
            facts.fact_value(
                entity=compartment,
                attribute=AvAttribute.TOKEN,
                authorization=authorization,
            ).decode_string()
        )
    else:
        raise AuthorizationError("invalid compartment")


def authenticated_token(
    comp_key: AvKey, identity_key: AvKey, ident_token: AvAuthorization
) -> AvAuthorization:
    """
    Retrieves the authenticated compartment token for an identity.
    
    Returns the compartment-specific token available to an authenticated
    identity, who is a member of the compartment.
    
    Args:
        comp_key (AvKey): Key identifier for the target compartment.
        identity_key (AvKey): Key identifier for the identity.
        ident_token (AvAuthorization): Identity's authentication token.
    
    Returns:
        AvAuthorization: The compartment access token for the identity.
    
    Example:
        >>> comp_token = authenticated_token("research-key", "user-key", token)
    """
    return AvAuthorization(
        invoke_entity(
            entity=access_outlet,
            method=AvMethod.GET,
            attribute=AvAttribute.COMPARTMENT,
            name=comp_key,
            key=identity_key,
            value=AvValue.encode_string(str(ident_token)),
            authorization=VERIFY_AUTHORIZATION,
        ).decode_string()
    )


def compartment_outlet(
    compartment: AvEntity, authorization: AvAuthorization
) -> AvEntity:
    """
    Retrieves the outlet entity associated with a compartment.
    
    Returns the activated outlet of the compartment
    
    Args:
        compartment (AvEntity): compartment to query for outlet.
        authorization (AvAuthorization): Authorization that is able to perform operation.
    
    Returns:
        AvEntity: The outlet entity associated with the compartment.
    
    Raises:
        AuthorizationError: When compartment is invalid or authorization lacks
                           outlet access privileges.
    
    Example:
        >>> outlet = compartment_outlet(research_comp, admin_auth)
    """
    if compartment_valid(compartment=compartment, authorization=authorization):
        return facts.fact_value(
            entity=compartment,
            attribute=AvAttribute.OUTLET,
            authorization=authorization,
        ).decode_entity()
    else:
        raise AuthorizationError("Invalid compartment")


def lookup_compartment(key: str, authorization: AvAuthorization) -> AvEntity:
    """
    Searches for a compartment by its key identifier.
    
    Performs lookup operation to find compartment with matching
    key identifier. Returns the compartment if found and accessible,
    or NULL_ENTITY if no matching compartment exists.
    
    Args:
        key (str): Key identifier to search for in compartment features.
        authorization (AvAuthorization): Authorization for performing lookup
                                       operations.
    
    Returns:
        AvEntity: compartment with matching key, or NULL_ENTITY if
                 not found.
    
    Example:
        >>> comp = lookup_compartment("research-key", search_auth)
        >>> if comp != NULL_ENTITY:
        ...     print(f"Found compartment: {comp}")
    """
    if features.feature_member(
        entity=access_outlet,
        attribute=AvAttribute.COMPARTMENT,
        key=key,
        authorization=authorization,
    ):
        return features.feature_value(
            entity=access_outlet,
            attribute=AvAttribute.COMPARTMENT,
            key=key,
            authorization=authorization,
        ).decode_entity()
    else:
        return NULL_ENTITY


def compartment_valid(compartment: AvEntity, authorization: AvAuthorization) -> bool:
    """
    Validates whether an entity is a compartment.
    
    Checks if the entity exists as a valid compartment. Returns True if the entity is
    found as a registered compartment, False otherwise.
    
    Args:
        compartment (AvEntity): Entity to validate as a compartment.
        authorization (AvAuthorization): Authorization capable of performing operation.
    
    Returns:
        bool: True if entity is valid compartment, False otherwise.
    
    Example:
        >>> is_valid = compartment_valid(suspected_comp, check_auth)
        >>> if is_valid:
        ...     print("Entity is valid compartment")
    """
    return (
        lookup_compartment(
            key=entity_key(entity=compartment, authorization=authorization),
            authorization=authorization,
        )
        != NULL_ENTITY
    )


def authenticated_outlet(comp_key: str, comp_token: AvAuthorization) -> AvEntity:
    """
    Retrieves the outlet for a compartment using token-based authentication.
    
    Returns the outlet entity associated with a compartment, accessed
    through compartment token authentication rather than direct entity
    reference. Enables outlet access through token-based workflows.
    
    Args:
        comp_key (str): Key identifier for the compartment.
        comp_token (AvAuthorization): Compartment token for authentication.
    
    Returns:
        AvEntity: The outlet entity for the authenticated compartment.
    
    Example:
        >>> outlet = authenticated_outlet("research-key", comp_token)
    """
    return invoke_entity(
        entity=access_outlet,
        method=AvMethod.GET,
        attribute=AvAttribute.OUTLET,
        name=comp_key,
        value=AvValue.encode_string(str(comp_token)),
        authorization=VERIFY_AUTHORIZATION,
    ).decode_entity()


def compartment_granted(compartment_key: str,
                        identity_key: str,
                        identity_token: AvAuthorization) -> bool:
    """
    Checks if an identity has been granted access to a compartment.
    
    Verifies whether the specified identity has compartment access by
    checking the compartment membership using identity token authentication.
    Returns True if access is granted, False otherwise.
    
    Args:
        compartment_key (str): Key identifier for the compartment.
        identity_key (str): Key identifier for the identity.
        identity_token (AvAuthorization): Identity's authentication token.
    
    Returns:
        bool: True if identity has compartment access, False otherwise.
    
    Example:
        >>> has_access = compartment_granted(
        ...     "research-key",
        ...     "user-key", 
        ...     user_token
        ... )
        >>> if has_access:
        ...     print("Identity has compartment access")
    """
    return invoke_entity(
        entity=access_outlet,
        method=AvMethod.MEMBER,
        attribute=AvAttribute.COMPARTMENT,
        name = compartment_key,
        key = identity_key,
        value = AvValue.encode_string(str(identity_token)),
        authorization=VERIFY_AUTHORIZATION,
    ).decode_boolean()