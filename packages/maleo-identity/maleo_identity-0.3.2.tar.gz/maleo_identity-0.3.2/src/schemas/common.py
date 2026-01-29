import json
from datetime import date
from pydantic import BaseModel, Field
from typing import Annotated
from nexo.enums.identity import OptRhesus, RhesusMixin
from nexo.enums.medical import MedicalRole
from nexo.enums.organization import (
    OrganizationRole,
    OrganizationRelation,
    SimpleOrganizationRelationMixin,
)
from nexo.enums.system import SystemRole
from nexo.enums.status import DataStatus as DataStatusEnum, SimpleDataStatusMixin
from maleo.metadata.schemas.blood_type import (
    OptKeyOrStandardSchema as BloodTypeOptKeyOrStandardSchema,
    FullBloodTypeMixin,
)
from maleo.metadata.schemas.gender import (
    OptKeyOrStandardSchema as GenderOptKeyOrStandardSchema,
    KeyOrStandardSchema as GenderKeyOrStandardSchema,
    FullGenderMixin,
)
from maleo.metadata.schemas.medical_role import (
    KeyOrStandardSchema as MedicalRoleKeyOrStandardSchema,
    FullMedicalRoleMixin,
)
from maleo.metadata.schemas.organization_role import (
    KeyOrStandardSchema as OrganizationRoleKeyOrStandardSchema,
    FullOrganizationRoleMixin,
)
from maleo.metadata.schemas.organization_type import (
    KeyOrStandardSchema as OrganizationTypeKeyOrStandardSchema,
    FullOrganizationTypeMixin,
)
from maleo.metadata.schemas.system_role import (
    KeyOrStandardSchema as SystemRoleKeyOrStandardSchema,
    FullSystemRoleMixin,
)
from maleo.metadata.schemas.user_type import (
    KeyOrStandardSchema as UserTypeKeyOrStandardSchema,
    FullUserTypeMixin,
)
from nexo.schemas.mixins.identity import (
    DataIdentifier,
    IntOrganizationId,
    IntUserId,
    BirthDate,
    DateOfBirth,
)
from nexo.schemas.mixins.timestamp import ActivationTimestamp
from nexo.types.datetime import OptDate
from nexo.types.integer import OptInt
from nexo.types.string import OptStr, ManyStrs
from ..enums.api_key import IdentifierType as APIKeyIdentifierType
from ..enums.organization_registration_code import (
    IdentifierType as OrganizationRegistrationCodeIdentifierType,
)
from ..enums.organization_relation import (
    IdentifierType as OrganizationRelationIdentifierType,
)
from ..enums.organization import IdentifierType as OrganizationIdentifierType
from ..enums.patient import IdentifierType as PatientIdentifierType
from ..enums.user_medical_role import IdentifierType as UserMedicalRoleIdentifierType
from ..enums.user_organization_role import (
    IdentifierType as UserOrganizationRoleIdentifierType,
)
from ..enums.user_organization import IdentifierType as UserOrganizationIdentifierType
from ..enums.user_profile import IdentifierType as UserProfileIdentifierType
from ..enums.user_system_role import IdentifierType as UserSystemRoleIdentifierType
from ..enums.user import IdentifierType as UserIdentifierType
from ..mixins.common import IdCard, FullName, BirthPlace, PlaceOfBirth
from ..mixins.api_key import APIKey
from ..mixins.organization_registration_code import Code, CurrentUses
from ..mixins.organization_relation import IsBidirectional, Meta
from ..mixins.organization import Key as OrganizationKey, Name as OrganizationName
from ..mixins.patient import PatientIdentity
from ..mixins.user_profile import (
    LeadingTitle,
    FirstName,
    MiddleName,
    LastName,
    EndingTitle,
    AvatarName,
    AvatarUrl,
)
from ..mixins.user import Username, Email, Phone, Password
from ..types.api_key import IdentifierValueType as APIKeyIdentifierValueType
from ..types.organization_registration_code import (
    IdentifierValueType as OrganizationRegistrationCodeIdentifierValueType,
)
from ..types.organization_relation import (
    IdentifierValueType as OrganizationRelationIdentifierValueType,
)
from ..types.organization import IdentifierValueType as OrganizationIdentifierValueType
from ..types.patient import IdentifierValueType as PatientIdentifierValueType
from ..types.user_medical_role import (
    IdentifierValueType as UserMedicalRoleIdentifierValueType,
)
from ..types.user_organization_role import (
    IdentifierValueType as UserOrganizationRoleIdentifierValueType,
)
from ..types.user_organization import (
    IdentifierValueType as UserOrganizationIdentifierValueType,
)
from ..types.user_profile import IdentifierValueType as UserProfileIdentifierValueType
from ..types.user_system_role import (
    IdentifierValueType as UserSystemRoleIdentifierValueType,
)
from ..types.user import IdentifierValueType as UserIdentifierValueType


class APIKeySchema(
    APIKey,
    IntOrganizationId[OptInt],
    IntUserId[int],
    SimpleDataStatusMixin[DataStatusEnum],
    DataIdentifier,
):
    @property
    def _identifiers(
        self,
    ) -> tuple[tuple[APIKeyIdentifierType, APIKeyIdentifierValueType], ...]:
        return (
            (APIKeyIdentifierType.ID, self.id),
            (APIKeyIdentifierType.UUID, str(self.uuid)),
            (APIKeyIdentifierType.API_KEY, self.api_key),
            (APIKeyIdentifierType.COMPOSITE, (self.user_id, self.organization_id)),
        )

    @property
    def cache_key_identifiers(self) -> ManyStrs:
        return tuple(
            '"identifier": '
            + json.dumps(
                {
                    "type": type.value,
                    "value": value,
                }
            )
            for type, value in self._identifiers
        )


class PatientSchema(
    RhesusMixin[OptRhesus],
    FullBloodTypeMixin[BloodTypeOptKeyOrStandardSchema],
    FullGenderMixin[GenderKeyOrStandardSchema],
    DateOfBirth[date],
    PlaceOfBirth[OptStr],
    FullName[str],
    PatientIdentity,
    IntOrganizationId[int],
    IntUserId[int],
    SimpleDataStatusMixin[DataStatusEnum],
    DataIdentifier,
):
    @property
    def _identifiers(
        self,
    ) -> tuple[tuple[PatientIdentifierType, PatientIdentifierValueType | str], ...]:
        return (
            (PatientIdentifierType.ID, self.id),
            (PatientIdentifierType.UUID, str(self.uuid)),
        )

    @property
    def cache_key_identifiers(self) -> ManyStrs:
        return tuple(
            '"identifier": '
            + json.dumps(
                {
                    "type": type.value,
                    "value": value,
                }
            )
            for type, value in self._identifiers
        )


class OrganizationRegistrationCodeSchema(
    CurrentUses,
    Code[str],
    IntOrganizationId[int],
    SimpleDataStatusMixin[DataStatusEnum],
    DataIdentifier,
):
    @property
    def _identifiers(
        self,
    ) -> tuple[
        tuple[
            OrganizationRegistrationCodeIdentifierType,
            OrganizationRegistrationCodeIdentifierValueType,
        ],
        ...,
    ]:
        return (
            (OrganizationRegistrationCodeIdentifierType.ID, self.id),
            (OrganizationRegistrationCodeIdentifierType.UUID, str(self.uuid)),
            (
                OrganizationRegistrationCodeIdentifierType.ORGANIZATION_ID,
                self.organization_id,
            ),
            (OrganizationRegistrationCodeIdentifierType.CODE, self.code),
        )

    @property
    def cache_key_identifiers(self) -> ManyStrs:
        return tuple(
            '"identifier": '
            + json.dumps(
                {
                    "type": type.value,
                    "value": value,
                }
            )
            for type, value in self._identifiers
        )


OptOrganizationRegistrationCodeSchema = OrganizationRegistrationCodeSchema | None


class OrganizationRegistrationCodeSchemaMixin(BaseModel):
    registration_code: Annotated[
        OptOrganizationRegistrationCodeSchema,
        Field(None, description="Organization's registration code"),
    ] = None


class OrganizationSchema(
    OrganizationName[str],
    OrganizationKey[str],
    FullOrganizationTypeMixin[OrganizationTypeKeyOrStandardSchema],
    SimpleDataStatusMixin[DataStatusEnum],
    DataIdentifier,
):
    @property
    def _identifiers(
        self,
    ) -> tuple[tuple[OrganizationIdentifierType, OrganizationIdentifierValueType], ...]:
        return (
            (OrganizationIdentifierType.ID, self.id),
            (OrganizationIdentifierType.UUID, str(self.uuid)),
            (OrganizationIdentifierType.KEY, self.key),
        )

    @property
    def cache_key_identifiers(self) -> ManyStrs:
        return tuple(
            '"identifier": '
            + json.dumps(
                {
                    "type": type.value,
                    "value": value,
                }
            )
            for type, value in self._identifiers
        )


class OrganizationSchemaMixin(BaseModel):
    organization: Annotated[OrganizationSchema, Field(..., description="Organization")]


class SourceOrganizationSchemaMixin(BaseModel):
    source: Annotated[OrganizationSchema, Field(..., description="Source organization")]


class SourceOrganizationRelationSchema(
    Meta,
    IsBidirectional[bool],
    SimpleOrganizationRelationMixin[OrganizationRelation],
    SourceOrganizationSchemaMixin,
    SimpleDataStatusMixin[DataStatusEnum],
    DataIdentifier,
):
    pass


class SourceOrganizationRelationsSchemaMixin(BaseModel):
    sources: Annotated[
        list[SourceOrganizationRelationSchema],
        Field(list[SourceOrganizationRelationSchema](), description="Sources"),
    ] = list[SourceOrganizationRelationSchema]()


class TargetOrganizationSchemaMixin(BaseModel):
    target: Annotated[OrganizationSchema, Field(..., description="Target organization")]


class TargetOrganizationRelationSchema(
    Meta,
    IsBidirectional[bool],
    SimpleOrganizationRelationMixin[OrganizationRelation],
    TargetOrganizationSchemaMixin,
    SimpleDataStatusMixin[DataStatusEnum],
    DataIdentifier,
):
    pass


class TargetOrganizationRelationsSchemaMixin(BaseModel):
    targets: Annotated[
        list[TargetOrganizationRelationSchema],
        Field(list[TargetOrganizationRelationSchema](), description="Targets"),
    ] = list[TargetOrganizationRelationSchema]()


class OrganizationRelationSchema(
    Meta,
    IsBidirectional[bool],
    SimpleOrganizationRelationMixin[OrganizationRelation],
    TargetOrganizationSchemaMixin,
    SourceOrganizationSchemaMixin,
    SimpleDataStatusMixin[DataStatusEnum],
    DataIdentifier,
):
    @property
    def _identifiers(
        self,
    ) -> tuple[
        tuple[
            OrganizationRelationIdentifierType,
            OrganizationRelationIdentifierValueType | str,
        ],
        ...,
    ]:
        return (
            (OrganizationRelationIdentifierType.ID, self.id),
            (OrganizationRelationIdentifierType.UUID, str(self.uuid)),
            (
                OrganizationRelationIdentifierType.COMPOSITE,
                (self.target.id, self.source.id, self.relation),
            ),
        )

    @property
    def cache_key_identifiers(self) -> ManyStrs:
        return tuple(
            '"identifier": '
            + json.dumps(
                {
                    "type": type.value,
                    "value": value,
                }
            )
            for type, value in self._identifiers
        )


class UserMedicalRoleSchema(
    FullMedicalRoleMixin[MedicalRoleKeyOrStandardSchema],
    IntOrganizationId[int],
    IntUserId[int],
    SimpleDataStatusMixin[DataStatusEnum],
    DataIdentifier,
):
    @property
    def _identifiers(
        self,
    ) -> tuple[
        tuple[UserMedicalRoleIdentifierType, UserMedicalRoleIdentifierValueType | str],
        ...,
    ]:
        return (
            (UserMedicalRoleIdentifierType.ID, self.id),
            (UserMedicalRoleIdentifierType.UUID, str(self.uuid)),
            (
                UserMedicalRoleIdentifierType.COMPOSITE,
                (
                    self.user_id,
                    self.organization_id,
                    (
                        self.medical_role
                        if isinstance(self.medical_role, MedicalRole)
                        else MedicalRole(self.medical_role.key)
                    ),
                ),
            ),
        )

    @property
    def cache_key_identifiers(self) -> ManyStrs:
        return tuple(
            '"identifier": '
            + json.dumps(
                {
                    "type": type.value,
                    "value": value,
                }
            )
            for type, value in self._identifiers
        )


class UserMedicalRolesSchemaMixin(BaseModel):
    medical_roles: Annotated[
        list[UserMedicalRoleSchema],
        Field(list[UserMedicalRoleSchema](), description="Medical roles"),
    ] = list[UserMedicalRoleSchema]()


class UserOrganizationRoleSchema(
    FullOrganizationRoleMixin[OrganizationRoleKeyOrStandardSchema],
    IntOrganizationId[int],
    IntUserId[int],
    SimpleDataStatusMixin[DataStatusEnum],
    DataIdentifier,
):
    @property
    def _identifiers(
        self,
    ) -> tuple[
        tuple[
            UserOrganizationRoleIdentifierType,
            UserOrganizationRoleIdentifierValueType | str,
        ],
        ...,
    ]:
        return (
            (UserOrganizationRoleIdentifierType.ID, self.id),
            (UserOrganizationRoleIdentifierType.UUID, str(self.uuid)),
            (
                UserOrganizationRoleIdentifierType.COMPOSITE,
                (
                    self.user_id,
                    self.organization_id,
                    (
                        self.organization_role
                        if isinstance(self.organization_role, OrganizationRole)
                        else OrganizationRole(self.organization_role.key)
                    ),
                ),
            ),
        )

    @property
    def cache_key_identifiers(self) -> ManyStrs:
        return tuple(
            '"identifier": '
            + json.dumps(
                {
                    "type": type.value,
                    "value": value,
                }
            )
            for type, value in self._identifiers
        )


class UserOrganizationRolesSchemaMixin(BaseModel):
    organization_roles: Annotated[
        list[UserOrganizationRoleSchema],
        Field(list[UserOrganizationRoleSchema](), description="Organization roles"),
    ] = list[UserOrganizationRoleSchema]()


class UserProfileSchema(
    AvatarUrl[OptStr],
    AvatarName[str],
    FullBloodTypeMixin[BloodTypeOptKeyOrStandardSchema],
    FullGenderMixin[GenderOptKeyOrStandardSchema],
    BirthDate[OptDate],
    BirthPlace[OptStr],
    FullName[str],
    EndingTitle[OptStr],
    LastName[str],
    MiddleName[OptStr],
    FirstName[str],
    LeadingTitle[OptStr],
    IdCard[OptStr],
    IntUserId[int],
    SimpleDataStatusMixin[DataStatusEnum],
    DataIdentifier,
):
    avatar_url: Annotated[OptStr, Field(None, description="Avatar URL")]

    @property
    def _identifiers(
        self,
    ) -> tuple[
        tuple[
            UserProfileIdentifierType,
            UserProfileIdentifierValueType,
        ],
        ...,
    ]:
        return (
            (UserProfileIdentifierType.ID, self.id),
            (UserProfileIdentifierType.UUID, str(self.uuid)),
            (UserProfileIdentifierType.USER_ID, self.user_id),
            (UserProfileIdentifierType.ID_CARD, self.id_card or ""),
        )

    @property
    def cache_key_identifiers(self) -> ManyStrs:
        return tuple(
            '"identifier": '
            + json.dumps(
                {
                    "type": type.value,
                    "value": value,
                }
            )
            for type, value in self._identifiers
        )


OptUserProfileSchema = UserProfileSchema | None


class UserProfileSchemaMixin(BaseModel):
    profile: Annotated[
        OptUserProfileSchema, Field(None, description="User's Profile")
    ] = None


class UserSystemRoleSchema(
    FullSystemRoleMixin[SystemRoleKeyOrStandardSchema],
    IntUserId[int],
    SimpleDataStatusMixin[DataStatusEnum],
    DataIdentifier,
):
    @property
    def _identifiers(
        self,
    ) -> tuple[
        tuple[UserSystemRoleIdentifierType, UserSystemRoleIdentifierValueType | str],
        ...,
    ]:
        return (
            (UserSystemRoleIdentifierType.ID, self.id),
            (UserSystemRoleIdentifierType.UUID, str(self.uuid)),
            (
                UserSystemRoleIdentifierType.COMPOSITE,
                (
                    self.user_id,
                    (
                        self.system_role
                        if isinstance(self.system_role, SystemRole)
                        else SystemRole(self.system_role.key)
                    ),
                ),
            ),
        )

    @property
    def cache_key_identifiers(self) -> ManyStrs:
        return tuple(
            '"identifier": '
            + json.dumps(
                {
                    "type": type.value,
                    "value": value,
                }
            )
            for type, value in self._identifiers
        )


class UserSystemRolesSchemaMixin(BaseModel):
    system_roles: Annotated[
        list[UserSystemRoleSchema],
        Field(
            list[UserSystemRoleSchema](),
            description="User's system roles",
            min_length=1,
        ),
    ] = list[UserSystemRoleSchema]()


class UserSchema(
    UserProfileSchemaMixin,
    Phone[str],
    Email[str],
    Username[str],
    FullUserTypeMixin[UserTypeKeyOrStandardSchema],
    SimpleDataStatusMixin[DataStatusEnum],
    ActivationTimestamp,
    DataIdentifier,
):
    @property
    def _identifiers(
        self,
    ) -> tuple[tuple[UserIdentifierType, UserIdentifierValueType], ...]:
        return (
            (UserIdentifierType.ID, self.id),
            (UserIdentifierType.UUID, str(self.uuid)),
            (UserIdentifierType.EMAIL, self.email),
            (UserIdentifierType.USERNAME, self.username),
        )

    @property
    def cache_key_identifiers(self) -> ManyStrs:
        return tuple(
            '"identifier": '
            + json.dumps(
                {
                    "type": type.value,
                    "value": value,
                }
            )
            for type, value in self._identifiers
        )


class UserSchemaMixin(BaseModel):
    user: Annotated[UserSchema, Field(..., description="User")]


class UserPasswordSchema(
    Password,
    SimpleDataStatusMixin[DataStatusEnum],
    DataIdentifier,
):
    pass


class VerifyPasswordSchema(BaseModel):
    is_valid: Annotated[bool, Field(..., description="Whether password is valid")]


class UserOrganizationSchema(
    UserMedicalRolesSchemaMixin,
    UserOrganizationRolesSchemaMixin,
    OrganizationSchemaMixin,
    UserSchemaMixin,
    SimpleDataStatusMixin[DataStatusEnum],
    DataIdentifier,
):
    @property
    def _identifiers(
        self,
    ) -> tuple[
        tuple[
            UserOrganizationIdentifierType, UserOrganizationIdentifierValueType | str
        ],
        ...,
    ]:
        return (
            (UserOrganizationIdentifierType.ID, self.id),
            (UserOrganizationIdentifierType.UUID, str(self.uuid)),
            (
                UserOrganizationIdentifierType.COMPOSITE,
                (self.user.id, self.organization.id),
            ),
        )

    @property
    def cache_key_identifiers(self) -> ManyStrs:
        return tuple(
            '"identifier": '
            + json.dumps(
                {
                    "type": type.value,
                    "value": value,
                }
            )
            for type, value in self._identifiers
        )
