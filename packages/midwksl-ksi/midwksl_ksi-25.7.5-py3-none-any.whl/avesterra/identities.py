""" 
Copyright (c) [Midwest Knowledge System Labs & Plex - Alexander Larkin] [2025-2026]
Copyright (c) [LEDR Technologies Inc.] [2024-2025]
This file is part of the Orchestra library, which helps developer use our Orchestra technology which is based on AvesTerra, owned and developed by Georgetown University, under license agreement with LEDR Technologies Inc.
The Orchestra library is a free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.
The Orchestra library is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.
You should have received a copy of the GNU Lesser General Public License along with the Orchestra library. If not, see <https://www.gnu.org/licenses/>.
If you have any questions, feedback or issues about the Orchestra library, you can contact us at support@midwksl.net.
"""

from avesterra.outlets import delete_outlet, create_outlet
from avesterra.avial import *
from avesterra.predefined import access_outlet
import avesterra.facts as facts
import avesterra.tokens as tokens
import avesterra.compartments as compartments
import avesterra.features as features


AvIdentity = AvEntity


def create_identity(
    name: str,
    key: str,
    email: str,
    authorization: AvAuthorization,
) -> AvEntity:
    """
    Creates a new identity in the AvesTerra distributed graph database.
    
    An identity represents a user account within the AvesTerra system, similar to
    a user on a computer system. Each identity has an associated identity token mapped to
    an identity authority, which is the backbone of identity level authorization. Only processes with
    Root Authority can create identities. The created identity must be validated
    before it can function properly through RSA keypair generation and password
    setting via the validation process.
    
    Args:
        name (str): Human-readable name identifier for the identity, stored in
                   the entity's Name metadata field.
        key (str): Unique key identifier for identity lookups, cannot be NULL_KEY.
        email (str): Email address associated with the identity account.
        authorization (AvAuthorization): Root Authority required
                                       to create identities.
    
    Returns:
        AvEntity: The newly created identity with unique EUID and
                 associated token/authority mapping.
    
    Raises:
        ValueError: When identity key is NULL_KEY (not allowed).
        AuthorizationError: When identity with key already exists or authorization
                           lacks identity creation privileges.
        EntityError: When identity creation fails due to system constraints.
    
    Example:
        >>> root_auth = AvAuthorization.simple("root-token")
        >>> user_identity = create_identity(
        ...     "John Doe",
        ...     "john-doe-key",
        ...     "john@example.com",
        ...     root_auth
        ... )
        >>> print(user_identity)
        <0|0|234567>
    """
    token: AvAuthorization = AvAuthorization.random()
    authority: AvAuthorization = AvAuthorization.random()
    validation: str = str(AvAuthorization.random())

    if key == NULL_KEY:
        raise ValueError("null identity key not allowed")

    if not features.feature_member(
        entity=access_outlet,
        attribute=AvAttribute.IDENTITY,
        key=key,
        authorization=authorization,
    ):
        # Create identity
        identity: AvEntity = create_entity(
            name=name,
            key=key,
            context=AvContext.AVESTERRA,
            category=AvCategory.AVESTERRA,
            klass=AvClass.IDENTITY,
            outlet=access_outlet,
            authorization=authorization,
        )

        # Authorize identity

        # Connect compartment adapter to identity
        connect_outlet(
            entity=identity, outlet=access_outlet, authorization=authorization
        )

        # Reference identity so it can survive a reboot
        reference_entity(entity=identity, authorization=authorization)

        # Invoke authentication adapter
        invoke_entity(
            entity=identity, method=AvMethod.CREATE, authorization=authorization
        )

        # Create identity outlet
        ident_outlet: AvEntity = create_outlet(
            name=name,
            key=key,
            context=AvContext.AVESTERRA,
            category=AvCategory.AVESTERRA,
            klass=AvClass.AVESTERRA,
            authorization=authorization,
        )

        # Change identity outlet authority to new identity authority
        change_entity(
            entity=ident_outlet, authority=authority, authorization=authorization
        )

        # Reference identity outlet so it can survive a reboot
        reference_entity(entity=ident_outlet, authorization=authorization)

        # Setup identity fields
        facts.set_fact(
            entity=identity,
            attribute=AvAttribute.TOKEN,
            value=AvValue.encode_string(str(token)),
            authorization=authorization,
        )
        facts.set_fact(
            entity=identity,
            attribute=AvAttribute.AUTHORITY,
            value=AvValue.encode_string(str(authority)),
            authorization=authorization,
        )
        facts.set_fact(
            entity=identity,
            attribute=AvAttribute.OUTLET,
            value=AvValue.encode(ident_outlet),
            authorization=authorization,
        )
        facts.set_fact(
            entity=identity,
            attribute=AvAttribute.COMPARTMENT,
            value=NULL_VALUE,
            authorization=authorization,
        )
        facts.set_fact(
            entity=identity,
            attribute=AvAttribute.EMAIL,
            value=AvValue.encode_string(email),
            authorization=authorization,
        )
        facts.set_fact(
            entity=identity,
            attribute=AvAttribute.PASSWORD,
            value=AvValue.encode_string(""),
            authorization=authorization,
        )
        facts.set_fact(
            entity=identity,
            attribute=AvAttribute.STATE,
            value=AvValue.encode_string("WARNING_STATE"),
            authorization=authorization,
        )
        facts.set_fact(
            entity=identity,
            attribute=AvAttribute.VALIDATION,
            value=AvValue.encode_string(validation),
            authorization=authorization,
        )

        # Self subscribe identity_outlet
        subscribe_event(
            entity=ident_outlet, outlet=ident_outlet, authorization=authority
        )

        # Put reference to identity in the authentication outlet
        features.set_feature(
            entity=access_outlet,
            attribute=AvAttribute.IDENTITY,
            name=name,
            key=key,
            value=AvValue.encode(identity),
            authorization=authorization,
        )

        # Enable map the identity's token to its
        # authority
        tokens.instate(token=token, authority=authority, authorization=authorization)
        return identity
    else:
        raise AuthorizationError("identity already exists")


def delete_identity(identity: AvEntity, authorization: AvAuthorization):
    """
    Permanently deletes an identity from the AvesTerra system.
    
    Removes the identity and cleans up all associated resources including associated
    token mappings, compartment memberships, outlet references, and its authority.
    
    Args:
        identity (AvEntity): Valid identity to delete.
        authorization (AvAuthorization): Root Authority required
                                       to delete identities.
    
    Raises:
        AuthorizationError: When identity is invalid or authorization lacks
                           identity deletion privileges.
        EntityError: When identity deletion fails due to system constraints.
    
    Example:
        >>> delete_identity(old_identity, root_auth)
    """
    # Get key of identity
    identity_key: str = entity_key(entity=identity, authorization=authorization)

    if identity_valid(identity=identity, authorization=authorization):
        # Get token of identity
        token: AvAuthorization = AvAuthorization(
            facts.fact_value(
                entity=identity,
                attribute=AvAttribute.TOKEN,
                authorization=authorization,
            ).decode_string()
        )

        # Disable the identity's token, so it cannot be used
        # as a substitute for the entity's authority
        tokens.destate(token=token, authorization=authorization)

        # Get identity's authority
        authority: AvAuthorization = AvAuthorization(
            facts.get_fact(
                entity=identity,
                attribute=AvAttribute.AUTHORITY,
                authorization=authorization,
            ).decode_string()
        )

        # Prevents identity's authority from being able to access
        # NULL ENTITY(Where token -> authority) mappings are stored
        deauthorize_entity(
            entity=NULL_ENTITY, authority=authority, authorization=authorization
        )

        # Make identity leave all compartments
        # that it is a member of
        while (
                features.feature_count(
                entity=identity,
                attribute=AvAttribute.COMPARTMENT,
                authorization=authorization,
            )
                != 0
        ):
            compartment: AvEntity = features.feature_value(
                entity=identity,
                attribute=AvAttribute.COMPARTMENT,
                authorization=authorization,
            ).decode_entity()

            compartments.revoke_compartment(
                compartment=compartment, identity=identity, authorization=authorization
            )

        # Remove identity from the compartment adapter
        features.exclude_feature(
            entity=access_outlet,
            attribute=AvAttribute.IDENTITY,
            key=identity_key,
            authorization=authorization,
        )

        # Get identity outlet from identity
        outlet: AvEntity = facts.fact_value(
            entity=identity, attribute=AvAttribute.OUTLET, authorization=authorization
        ).decode_entity()

        # Dereference identity outlet
        # so that it can be deleted
        dereference_entity(entity=outlet, authorization=authorization)

        # Delete identity outlet
        delete_outlet(outlet=outlet, authorization=authorization)

        # Dereference identity so that it can
        # be deleted
        dereference_entity(entity=identity, authorization=authorization)

        # Delete identity
        delete_entity(entity=identity, authorization=authorization)
    else:
        raise AuthorizationError("invalid identity")


def reset_password(identity: AvEntity, authorization: AvAuthorization):
    """
    Resets the password for an identity, requiring re-validation.
    
    Clears the current password hash and generates a new validation token,
    putting the identity into WARNING_STATE. The identity must complete
    the validation process with the new validation token before it can
    function normally again.
    
    Args:
        identity (AvEntity): Valid identity to reset password for.
        authorization (AvAuthorization): Authorization with sufficient authorization
                                       to modify identity password settings.
    
    Raises:
        AuthorizationError: When identity is invalid or authorization lacks
                           password reset privileges.
    
    Example:
        >>> reset_password(user_identity, admin_auth)
    """
    validation: str = str(AvAuthorization.random())

    if identity_valid(identity=identity, authorization=authorization):
        # Empty out password hash
        facts.set_fact(
            entity=identity,
            attribute=AvAttribute.PASSWORD,
            value=AvValue.encode_string(""),
            authorization=authorization,
        )

        # Set new validation token
        facts.set_fact(
            entity=identity,
            attribute=AvAttribute.VALIDATION,
            value=AvValue.encode_string(str(validation)),
            authorization=authorization,
        )

        # Put entity into warning state; must validate
        # to put it into "GOOD" state
        facts.set_fact(
            entity=identity,
            attribute=AvAttribute.STATE,
            value=AvValue.encode_string("WARNING_STATE"),
            authorization=authorization,
        )
    else:
        raise AuthorizationError("invalid identity")


def identity_authority(
    identity: AvEntity, authorization: AvAuthorization
) -> AvAuthorization:
    """
    Retrieves the Authority for an identity.
    
    Returns the 128-bit Authority that represents the identity's
    access privileges within the AvesTerra system. This authority is used
    when the identity's token is resolved during server-side operations.
    
    Args:
        identity (AvEntity): identity to query for authority information.
        authorization (AvAuthorization): Authorization with sufficient authorization
                                       to access the authority of an identity.
    
    Returns:
        AvAuthorization: The Authority for the identity.
    
    Raises:
        AuthorizationError: When identity is invalid or authorization lacks
                           authority access privileges.
    
    Example:
        >>> authority = identity_authority(user_identity, admin_auth)
        >>> print(f"Identity authority: {authority}")
    """
    if identity_valid(identity=identity, authorization=authorization):
        return AvAuthorization(
            facts.fact_value(
                entity=identity,
                attribute=AvAttribute.AUTHORITY,
                authorization=authorization,
            ).decode_string()
        )
    else:
        raise AuthorizationError("invalid identity")


def authenticated_authority(
    identity_key: AvKey, ident_token: AvAuthorization
) -> AvAuthorization:
    """
    Retrieves the authority for an identity using its token.
    
    Returns the Authority of an identity enabling authority resolution through its token
    
    Args:
        identity_key (AvKey): Key identifier for the target identity.
        ident_token (AvAuthorization): Identity's authentication token.
    
    Returns:
            AvAuthorization: The Authority of the identity
    
    Example:
        >>> auth = authenticated_authority("john-doe-key", user_token)
    """
    return AvAuthorization(
        invoke_entity(
            entity=access_outlet,
            method=AvMethod.GET,
            attribute=AvAttribute.AUTHENTICATION,
            key=identity_key,
            value=AvValue.encode_string(str(ident_token)),
            authorization=VERIFY_AUTHORIZATION,
        ).decode_string()
    )


def identity_token(
    identity: AvEntity, authorization: AvAuthorization
) -> AvAuthorization:
    """
    Retrieves the identity token of an identity.
    
    Returns the identity's token stored in the TOKEN fact and maps to the identity's authority.
   
    Args:
        identity (AvEntity): identity to query for token information.
        authorization (AvAuthorization): Authorization with sufficient authorization
                                       to access the identity token.
    
    Returns:
        AvAuthorization: The identity token for the identity.
    
    Raises:
        AuthorizationError: When identity is invalid or authorization lacks
                           token access privileges.
    
    Example:
        >>> token = identity_token(user_identity, admin_auth)
    """
    if identity_valid(identity=identity, authorization=authorization):
        return AvAuthorization(
            facts.fact_value(
                entity=identity,
                attribute=AvAttribute.TOKEN,
                authorization=authorization,
            ).decode_string()
        )
    else:
        raise AuthorizationError("invalid identity")


def authenticated_token(identity_key: AvKey, password: str) -> AvAuthorization:
    """
    Authenticates an identity and retrieves its identity token using password verification.
    
    Performs password-based authentication against an identity and returns
    the identity's token if the correct password is provided. This is the
    primary method for gaining access to an identity's token.
    
    Args:
        identity_key (AvKey): Key identifier for the target identity.
        password (str): Password for identity authentication.
    
    Returns:
        AvAuthorization: The identity token upon successful authentication.
    
    Raises:
        AuthorizationError: When authentication fails due to invalid password
                           or identity key.
    
    Example:
        >>> user_token = authenticated_token("john-doe-key", "secret123")
    """
    return AvAuthorization(
        invoke_entity(
            entity=access_outlet,
            method=AvMethod.GET,
            attribute=AvAttribute.IDENTITY,
            key=identity_key,
            value=AvValue.encode_string(password),
            authorization=VERIFY_AUTHORIZATION,
        ).decode_string()
    )


def identity_outlet(identity: AvEntity, authorization: AvAuthorization) -> AvEntity:
    """
    Retrieves the outlet associated with an identity.
    
    Returns the activated outlet stored in the identity's OUTLET fact.
    
    Args:
        identity (AvEntity): identity to query for outlet information.
        authorization (AvAuthorization): Authorization with sufficient authorization
                                       to access identity outlet metadata.
    
    Returns:
        AvEntity: The outlet associated with the identity.
    
    Raises:
        AuthorizationError: When identity is invalid or authorization lacks
                           outlet access privileges.
    
    Example:
        >>> outlet = identity_outlet(user_identity, admin_auth)
    """
    if identity_valid(identity=identity, authorization=authorization):
        return facts.fact_value(
            entity=identity, attribute=AvAttribute.OUTLET, authorization=authorization
        ).decode_entity()
    else:
        raise AuthorizationError("Invalid identity")


def change_password(
    identity_key: str,
    old_password: str,
    new_password: str,
    ident_token: AvAuthorization,
):
    """
    Changes the password for an identity using token-based authentication.
    
    Updates an identity's password by verifying the old password and setting
    a new password. The current identity token must be provided for authentication purposes
    and the old password must match the current password for the operation
    to succeed.
    
    Args:
        identity_key (str): Key identifier for the target identity.
        old_password (str): Current password for verification (padded to 32 chars).
        new_password (str): New password to set (padded to 32 chars).
        ident_token (AvAuthorization): Identity token for authentication.
    
    Raises:
        AuthorizationError: When old password verification fails or token
                           is invalid.
    
    Example:
        >>> change_password(
        ...     "john-doe-key",
        ...     "old_secret",
        ...     "new_secret123",
        ...     user_token
        ... )
    """
    password = f"{old_password.ljust(32, ' ')}{new_password.ljust(32, ' ')}"

    invoke_entity(
        entity=access_outlet,
        method=AvMethod.SET,
        name=password,
        key=identity_key,
        value=AvValue.encode_string(str(ident_token)),
        authorization=VERIFY_AUTHORIZATION,
    )


def validate_identity_trick(identity: AvEntity, authorization: AvAuthorization):
    """
    Administrative function to manually validate an identity.
    
    Sets the identity state to GOOD_STATE, bypassing the normal validation
    process. This is an administrative override function that should be used
    carefully as it skips the standard RSA keypair validation workflow.
    
    Args:
        identity (AvEntity): identity to validate.
        authorization (AvAuthorization): Authorization with sufficient authorization
                                       to modify identity state.
    
    Example:
        >>> validate_identity_trick(user_identity, admin_auth)
    """
    facts.set_fact(
        entity=identity,
        attribute=AvAttribute.STATE,
        value=AvValue.encode_string("GOOD_STATE"),
        authorization=authorization,
    )


def lookup_identity(key: str, authorization: AvAuthorization) -> AvEntity:
    """
    Searches for an identity by its key identifier.
    
    Performs lookup operation to find identity with matching key
    identifier. Returns the identity if found and accessible,
    or NULL_ENTITY if no matching identity exists or access is denied.
    
    Args:
        key (str): Key identifier to search for in identity features.
        authorization (AvAuthorization): Authorization for performing lookup
                                       operations and accessing found identity.
    
    Returns:
        AvEntity: identity with matching key, or NULL_ENTITY if
                 not found or inaccessible.
    
    Example:
        >>> identity = lookup_identity("john-doe-key", search_auth)
        >>> if identity != NULL_ENTITY:
        ...     print(f"Found identity: {identity}")
    """
    if features.feature_member(
        entity=access_outlet,
        attribute=AvAttribute.IDENTITY,
        key=key,
        authorization=authorization,
    ):
        return features.feature_value(
            entity=access_outlet,
            attribute=AvAttribute.IDENTITY,
            key=key,
            authorization=authorization,
        ).decode_entity()
    else:
        return NULL_ENTITY


def identity_valid(identity: AvEntity, authorization: AvAuthorization) -> bool:
    """
    Validates whether an entity is a properly configured identity.
    
    Checks if the entity exists as a valid identity by performing key-based
    lookup verification. Returns True if the entity is found as a registered
    identity, False otherwise.
    
    Args:
        identity (AvEntity): Entity to validate as an identity.
        authorization (AvAuthorization): Authorization for accessing and
                                       validating the identity.
    
    Returns:
        bool: True if entity is valid identity, False otherwise.
    
    Example:
        >>> is_valid = identity_valid(suspected_identity, check_auth)
        >>> if is_valid:
        ...     print("Entity is valid identity")
    """
    return (
        lookup_identity(
            key=entity_key(entity=identity, authorization=authorization),
            authorization=authorization,
        )
        != NULL_ENTITY
    )


def identity_state(identity: AvEntity, authorization: AvAuthorization) -> AvState:
    """
    Retrieves the current state of an identity.
    
    Returns the identity's validation state, which indicates whether the
    identity is in GOOD_STATE (validated and functional) or WARNING_STATE
    (requires validation). Unvalidated identities have tokens that cannot
    resolve to authority or access compartments.
    
    Args:
        identity (AvEntity): identity to query for state information.
        authorization (AvAuthorization): Authorization with sufficient authorization
                                       to access identity state metadata.
    
    Returns:
        AvState: The current state of the identity (GOOD_STATE or WARNING_STATE).
    
    Example:
        >>> state = identity_state(user_identity, admin_auth)
        >>> if state == AvState.WARNING_STATE:
        ...     print("Identity requires validation")
    """
    return AvState[
        facts.fact_value(entity=identity, authorization=authorization).decode_integer()
    ]


def authenticated_outlet(identity_key: str, ident_token: AvAuthorization) -> AvEntity:
    """
    Retrieves the outlet for an identity using token-based authentication.
    
    Returns the outlet associated with an identity, accessed through
    identity token authentication rather than direct entity reference.
    Enables outlet access through token-based authentication workflows.
    
    Args:
        identity_key (str): Key identifier for the target identity.
        ident_token (AvAuthorization): Identity token for authentication.
    
    Returns:
        AvEntity: The outlet for the authenticated identity.
    
    Example:
        >>> outlet = authenticated_outlet("john-doe-key", user_token)
    """
    return invoke_entity(
        entity=access_outlet,
        method=AvMethod.GET,
        attribute=AvAttribute.OUTLET,
        name=identity_key,
        value=AvValue.encode_string(str(ident_token)),
        authorization=VERIFY_AUTHORIZATION,
    ).decode_entity()