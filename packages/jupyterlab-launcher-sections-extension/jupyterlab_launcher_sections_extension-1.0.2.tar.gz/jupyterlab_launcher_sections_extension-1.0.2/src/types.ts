/**
 * Configuration for a launcher section icon.
 */
export interface ISectionConfig {
  /**
   * Name of the launcher section (e.g., "Notebook", "Console", "Other")
   */
  section: string;

  /**
   * Inline SVG content for the section icon.
   * If not provided, the default icon is used.
   */
  icon?: string;

  /**
   * Tooltip text displayed on hover.
   */
  tooltip?: string;
}

/**
 * Response from the server config endpoint.
 */
export interface IConfigResponse {
  sections: ISectionConfig[];
}
