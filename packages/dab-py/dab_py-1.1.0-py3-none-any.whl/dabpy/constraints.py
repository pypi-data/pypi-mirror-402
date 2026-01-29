class Constraints:
    """
    WHOS API constraints for features and observations.
    Handles optional parameters for features and observations queries.
    """
    def __init__(
        self,
        bbox=None,
        observedProperty=None,
        ontology=None,
        country=None,
        provider=None,
        feature=None,
        localFeatureIdentifier=None,
        observationIdentifier=None,
        beginPosition=None,
        endPosition=None,
        spatialRelation=None,
        predefinedLayer=None,
        timeInterpolation=None,
        intendedObservationSpacing=None,
        aggregationDuration=None,
        limit=None,
        format=None
    ):
        self.bbox = bbox
        self.observedProperty = observedProperty
        self.ontology = ontology
        self.country = country
        self.provider = provider
        self.feature = feature
        self.localFeatureIdentifier = localFeatureIdentifier
        self.observationIdentifier = observationIdentifier
        self.beginPosition = beginPosition
        self.endPosition = endPosition
        self.spatialRelation = spatialRelation
        self.predefinedLayer = predefinedLayer
        self.timeInterpolation = timeInterpolation
        self.intendedObservationSpacing = intendedObservationSpacing
        self.aggregationDuration = aggregationDuration
        self.limit = limit
        self.format = format

    def to_query(self):
        """Build URL query string including only set parameters."""
        query_parts = []

        if self.bbox:
            south, west, north, east = self.bbox
            query_parts.append(f"west={west}")
            query_parts.append(f"south={south}")
            query_parts.append(f"east={east}")
            query_parts.append(f"north={north}")
        if self.observedProperty:
            query_parts.append(f"observedProperty={self.observedProperty}")
        if self.ontology:
            query_parts.append(f"ontology={self.ontology}")
        if self.country:
            query_parts.append(f"country={self.country}")
        if self.provider:
            query_parts.append(f"provider={self.provider}")
        if self.feature:
            query_parts.append(f"feature={self.feature}")
        if self.localFeatureIdentifier:
            query_parts.append(f"localFeatureIdentifier={self.localFeatureIdentifier}")
        if self.observationIdentifier:
            query_parts.append(f"observationIdentifier={self.observationIdentifier}")
        if self.beginPosition:
            query_parts.append(f"beginPosition={self.beginPosition}")
        if self.endPosition:
            query_parts.append(f"endPosition={self.endPosition}")
        if self.spatialRelation:
            query_parts.append(f"spatialRelation={self.spatialRelation}")
        if self.predefinedLayer:
            query_parts.append(f"predefinedLayer={self.predefinedLayer}")
        if self.timeInterpolation:
            query_parts.append(f"timeInterpolation={self.timeInterpolation}")
        if self.intendedObservationSpacing:
            query_parts.append(f"intendedObservationSpacing={self.intendedObservationSpacing}")
        if self.aggregationDuration:
            query_parts.append(f"aggregationDuration={self.aggregationDuration}")
        if self.limit is not None:
            query_parts.append(f"limit={self.limit}")
        if self.format:
            query_parts.append(f"format={self.format}")

        return "&".join(query_parts)


class DownloadConstraints(Constraints):
    """
    Extends Constraints with download-specific parameters:
    asynchDownloadName, eMailNotifications, useCache
    """
    def __init__(
        self,
        base_constraints: Constraints = None,
        asynchDownloadName=None,
        eMailNotifications=None,
        useCache=None,
        **kwargs
    ):
        # Initialize the parent Constraints attributes
        if base_constraints:
            super().__init__(**base_constraints.__dict__)
        else:
            super().__init__(**kwargs)

        # Download-specific fields
        self.asynchDownloadName = asynchDownloadName
        self.eMailNotifications = eMailNotifications
        self.useCache = useCache

    def to_query(self):
        """Build query string including inherited Constraints fields + download-specific ones."""
        query = super().to_query()  # get all inherited fields first
        extra = []

        if self.asynchDownloadName:
            extra.append(f"asynchDownloadName={self.asynchDownloadName}")
        if self.eMailNotifications is not None:
            extra.append(f"eMailNotifications={str(self.eMailNotifications).lower()}")
        if self.useCache is not None:
            extra.append(f"useCache={str(self.useCache).lower()}")

        if extra:
            query += "&" + "&".join(extra)

        return query