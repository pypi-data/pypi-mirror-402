/**
 * Comprehensive Test Suite for Dynamic Weight Configuration System
 * 
 * QA Testing Specialist - Enterprise Grade Validation Framework
 * 
 * Tests for:
 * - Weight configuration loading and validation
 * - Framework-specific weight variations
 * - Environment-based weight adjustments
 * - Custom override functionality
 * - Boundary conditions and error handling
 * - Performance and consistency validation
 */

import { describe, test, expect, beforeEach } from '@jest/jest';
import {
  getWeightConfig,
  validateWeightConfig,
  loadWeightConfigFromEnv,
  ComplianceFramework,
  EnvironmentType,
  OrganizationSize,
  FRAMEWORK_WEIGHTS,
  ENVIRONMENT_MODIFIERS,
  SIZE_MODIFIERS,
  WeightConfig
} from '../weight_config.js';

describe('Dynamic Weight Configuration System', () => {
  
  describe('Weight Configuration Loading', () => {
    test('should load default AWS Well-Architected weights', () => {
      const config = getWeightConfig();
      
      expect(config.organization_created).toBe(6);
      expect(config.management_account_created).toBe(6);
      expect(config.cloudtrail_created).toBe(6);
      expect(config.iam_users_removed).toBe(4);
      expect(config.ec2_instances_removed).toBe(4);
    });
    
    test('should load SOC2 framework weights with enhanced security focus', () => {
      const config = getWeightConfig(ComplianceFramework.SOC2);
      
      // SOC2 should have higher security-focused weights
      expect(config.securityhub_org_service_enabled).toBe(6);
      expect(config.iam_access_analyzer_org_service_enabled).toBe(6);
      expect(config.backup_policy_enabled).toBe(6);
      expect(config.guardduty_org_service_enabled).toBe(6);
      
      // Management account hygiene should be higher for SOC2
      expect(config.iam_users_removed).toBe(5);
      expect(config.ec2_instances_removed).toBe(5);
      expect(config.vpc_removed).toBe(5);
    });
    
    test('should load PCI-DSS framework weights with network isolation focus', () => {
      const config = getWeightConfig(ComplianceFramework.PCI_DSS);
      
      // PCI-DSS should emphasize network isolation
      expect(config.iam_users_removed).toBe(6);
      expect(config.ec2_instances_removed).toBe(6);
      expect(config.vpc_removed).toBe(6);
      
      // Enhanced security services
      expect(config.securityhub_org_service_enabled).toBe(6);
      expect(config.guardduty_org_service_enabled).toBe(6);
      expect(config.backup_policy_enabled).toBe(6);
    });
    
    test('should load HIPAA framework weights with data protection focus', () => {
      const config = getWeightConfig(ComplianceFramework.HIPAA);
      
      // HIPAA should emphasize data protection
      expect(config.backup_policy_enabled).toBe(6);
      expect(config.backup_org_service_enabled).toBe(6);
      expect(config.config_org_service_enabled).toBe(6);
      
      // Audit and logging
      expect(config.cloudtrail_created).toBe(6);
      expect(config.config_recorder_management).toBe(6);
      expect(config.config_delivery_channel_management).toBe(6);
    });
  });
  
  describe('Environment-Based Weight Adjustments', () => {
    test('should apply development environment modifier (20% reduction)', () => {
      const config = getWeightConfig(
        ComplianceFramework.AWS_WELL_ARCHITECTED,
        EnvironmentType.DEVELOPMENT
      );
      
      // 6 * 0.8 = 4.8, rounded to 5
      expect(config.organization_created).toBe(5);
      expect(config.management_account_created).toBe(5);
      
      // 4 * 0.8 = 3.2, rounded to 3
      expect(config.iam_users_removed).toBe(3);
    });
    
    test('should apply staging environment modifier (10% reduction)', () => {
      const config = getWeightConfig(
        ComplianceFramework.AWS_WELL_ARCHITECTED,
        EnvironmentType.STAGING
      );
      
      // 6 * 0.9 = 5.4, rounded to 5
      expect(config.organization_created).toBe(5);
      
      // 4 * 0.9 = 3.6, rounded to 4
      expect(config.iam_users_removed).toBe(4);
    });
    
    test('should apply production environment modifier (no reduction)', () => {
      const config = getWeightConfig(
        ComplianceFramework.AWS_WELL_ARCHITECTED,
        EnvironmentType.PRODUCTION
      );
      
      // Full weights for production
      expect(config.organization_created).toBe(6);
      expect(config.iam_users_removed).toBe(4);
    });
    
    test('should apply sandbox environment modifier (40% reduction)', () => {
      const config = getWeightConfig(
        ComplianceFramework.AWS_WELL_ARCHITECTED,
        EnvironmentType.SANDBOX
      );
      
      // 6 * 0.6 = 3.6, rounded to 4
      expect(config.organization_created).toBe(4);
      
      // 4 * 0.6 = 2.4, rounded to 2
      expect(config.iam_users_removed).toBe(2);
    });
  });
  
  describe('Organization Size-Based Adjustments', () => {
    test('should adjust weights for large organizations', () => {
      const config = getWeightConfig(
        ComplianceFramework.AWS_WELL_ARCHITECTED,
        EnvironmentType.PRODUCTION,
        OrganizationSize.LARGE
      );
      
      // Large orgs should have enhanced governance
      expect(config.scp_enabled).toBe(7); // Base 6 + 1
      expect(config.tag_policy_enabled).toBe(7); // Base 6 + 1
      expect(config.backup_policy_enabled).toBe(6); // Base 5 + 1
    });
    
    test('should adjust weights for enterprise organizations', () => {
      const config = getWeightConfig(
        ComplianceFramework.AWS_WELL_ARCHITECTED,
        EnvironmentType.PRODUCTION,
        OrganizationSize.ENTERPRISE
      );
      
      // Enterprise requires maximum governance
      expect(config.scp_enabled).toBe(7); // Base 6 + 1
      expect(config.tag_policy_enabled).toBe(7); // Base 6 + 1
      expect(config.backup_policy_enabled).toBe(6); // Base 5 + 1
      expect(config.control_tower_deployed).toBe(7); // Base 6 + 1
      expect(config.security_ou_deployed).toBe(7); // Base 6 + 1
    });
    
    test('should adjust weights for small organizations', () => {
      const config = getWeightConfig(
        ComplianceFramework.AWS_WELL_ARCHITECTED,
        EnvironmentType.PRODUCTION,
        OrganizationSize.SMALL
      );
      
      // Small orgs might not need all enterprise features
      expect(config.infrastructure_ou_deployed).toBe(4); // Base 5 - 1
      expect(config.workloads_ou_deployed).toBe(4); // Base 5 - 1
      expect(config.backup_policy_enabled).toBe(4); // Base 5 - 1
    });
  });
  
  describe('Custom Override Functionality', () => {
    test('should apply custom weight overrides', () => {
      const customOverrides: Partial<WeightConfig> = {
        organization_created: 8,
        cloudtrail_created: 10,
        iam_users_removed: 1
      };
      
      const config = getWeightConfig(
        ComplianceFramework.AWS_WELL_ARCHITECTED,
        EnvironmentType.PRODUCTION,
        OrganizationSize.MEDIUM,
        customOverrides
      );
      
      // Custom overrides should take precedence
      expect(config.organization_created).toBe(8);
      expect(config.cloudtrail_created).toBe(10);
      expect(config.iam_users_removed).toBe(1);
      
      // Non-overridden values should use defaults
      expect(config.management_account_created).toBe(6);
    });
  });
  
  describe('Weight Validation', () => {
    test('should validate correct weight configuration', () => {
      const validConfig: WeightConfig = {
        organization_created: 6,
        management_account_created: 6,
        iam_users_removed: 4,
        ec2_instances_removed: 4,
        vpc_removed: 4,
        legacy_cur_setup: 4,
        cloudtrail_created: 6,
        cloudtrail_org_service_enabled: 6,
        cloudtrail_org_trail_deployed: 6,
        config_recorder_management: 6,
        config_delivery_channel_management: 6,
        cloudformation_stacksets_activated: 5,
        guardduty_org_service_enabled: 4,
        ram_org_service_enabled: 4,
        securityhub_org_service_enabled: 4,
        iam_access_analyzer_org_service_enabled: 4,
        config_org_service_enabled: 4,
        cloudformation_org_service_enabled: 5,
        backup_org_service_enabled: 4,
        infrastructure_ou_deployed: 5,
        security_ou_deployed: 6,
        workloads_ou_deployed: 5,
        iam_idc_org_service_enabled: 6,
        iam_idc_configured: 6,
        scp_enabled: 6,
        tag_policy_enabled: 6,
        backup_policy_enabled: 5,
        control_tower_deployed: 6,
        control_tower_latest_version: 5,
        control_tower_not_drifted: 6,
        log_archive_account_deployed: 6,
        audit_account_deployed: 6
      };
      
      const result = validateWeightConfig(validConfig);
      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });
    
    test('should detect invalid weight values', () => {
      const invalidConfig: WeightConfig = {
        ...FRAMEWORK_WEIGHTS[ComplianceFramework.AWS_WELL_ARCHITECTED],
        organization_created: 0, // Too low
        management_account_created: 11, // Too high
        iam_users_removed: 3.5 // Not integer
      };
      
      const result = validateWeightConfig(invalidConfig);
      expect(result.valid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
      
      expect(result.errors).toContain(
        expect.stringContaining('organization_created must be between 1 and 10')
      );
      expect(result.errors).toContain(
        expect.stringContaining('management_account_created must be between 1 and 10')
      );
      expect(result.errors).toContain(
        expect.stringContaining('iam_users_removed must be an integer')
      );
    });
  });
  
  describe('Environment Variable Loading', () => {
    beforeEach(() => {
      // Clean up environment variables
      delete process.env.CFAT_COMPLIANCE_FRAMEWORK;
      delete process.env.CFAT_ENVIRONMENT_TYPE;
      delete process.env.CFAT_ORG_SIZE;
      delete process.env.CFAT_WEIGHT_OVERRIDES;
    });
    
    test('should load default values when no environment variables set', () => {
      const config = loadWeightConfigFromEnv();
      
      expect(config.framework).toBe(ComplianceFramework.AWS_WELL_ARCHITECTED);
      expect(config.environment).toBe(EnvironmentType.PRODUCTION);
      expect(config.orgSize).toBe(OrganizationSize.MEDIUM);
      expect(config.customOverrides).toEqual({});
    });
    
    test('should load values from environment variables', () => {
      process.env.CFAT_COMPLIANCE_FRAMEWORK = 'soc2';
      process.env.CFAT_ENVIRONMENT_TYPE = 'staging';
      process.env.CFAT_ORG_SIZE = 'large';
      process.env.CFAT_WEIGHT_OVERRIDES = '{"organization_created": 8}';
      
      const config = loadWeightConfigFromEnv();
      
      expect(config.framework).toBe(ComplianceFramework.SOC2);
      expect(config.environment).toBe(EnvironmentType.STAGING);
      expect(config.orgSize).toBe(OrganizationSize.LARGE);
      expect(config.customOverrides).toEqual({ organization_created: 8 });
    });
    
    test('should handle invalid JSON in weight overrides', () => {
      process.env.CFAT_WEIGHT_OVERRIDES = 'invalid json';
      
      const config = loadWeightConfigFromEnv();
      
      // Should fall back to empty overrides
      expect(config.customOverrides).toEqual({});
    });
  });
  
  describe('Framework Coverage Validation', () => {
    test('should have all required weights for each framework', () => {
      const requiredWeights = [
        'organization_created',
        'management_account_created',
        'cloudtrail_created',
        'control_tower_deployed',
        'security_ou_deployed',
        'log_archive_account_deployed',
        'audit_account_deployed'
      ];
      
      Object.values(ComplianceFramework).forEach(framework => {
        const weights = FRAMEWORK_WEIGHTS[framework];
        
        requiredWeights.forEach(weight => {
          expect(weights[weight as keyof WeightConfig]).toBeDefined();
          expect(typeof weights[weight as keyof WeightConfig]).toBe('number');
          expect(weights[weight as keyof WeightConfig]).toBeGreaterThanOrEqual(1);
          expect(weights[weight as keyof WeightConfig]).toBeLessThanOrEqual(10);
        });
      });
    });
  });
  
  describe('Performance and Consistency Testing', () => {
    test('should load configuration quickly', () => {
      const startTime = performance.now();
      
      for (let i = 0; i < 1000; i++) {
        getWeightConfig();
      }
      
      const endTime = performance.now();
      const avgTime = (endTime - startTime) / 1000;
      
      // Should average less than 1ms per configuration load
      expect(avgTime).toBeLessThan(1);
    });
    
    test('should produce consistent results for same parameters', () => {
      const config1 = getWeightConfig(
        ComplianceFramework.SOC2,
        EnvironmentType.STAGING,
        OrganizationSize.LARGE
      );
      
      const config2 = getWeightConfig(
        ComplianceFramework.SOC2,
        EnvironmentType.STAGING,
        OrganizationSize.LARGE
      );
      
      expect(config1).toEqual(config2);
    });
  });
  
  describe('Boundary Conditions and Error Handling', () => {
    test('should handle minimum weight values correctly', () => {
      const config = getWeightConfig(
        ComplianceFramework.CUSTOM,
        EnvironmentType.SANDBOX,
        OrganizationSize.SMALL,
        { organization_created: 1 }
      );
      
      // Should never go below 1
      expect(config.organization_created).toBeGreaterThanOrEqual(1);
    });
    
    test('should handle maximum organization size adjustments', () => {
      const config = getWeightConfig(
        ComplianceFramework.AWS_WELL_ARCHITECTED,
        EnvironmentType.PRODUCTION,
        OrganizationSize.ENTERPRISE
      );
      
      // Weights should remain reasonable even with maximum adjustments
      Object.values(config).forEach(weight => {
        expect(weight).toBeGreaterThanOrEqual(1);
        expect(weight).toBeLessThanOrEqual(10);
      });
    });
  });
});

/**
 * Integration tests for CFAT app.ts usage
 */
describe('CFAT App Integration', () => {
  test('should provide weights for all CFAT checks', () => {
    const config = getWeightConfig();
    
    // Test that we have all the weights needed by CFAT app
    const cfatRequiredWeights = [
      'organization_created',
      'management_account_created',
      'iam_users_removed',
      'ec2_instances_removed',
      'vpc_removed',
      'legacy_cur_setup',
      'cloudtrail_created',
      'cloudtrail_org_service_enabled',
      'cloudtrail_org_trail_deployed',
      'config_recorder_management',
      'config_delivery_channel_management',
      'cloudformation_stacksets_activated',
      'guardduty_org_service_enabled',
      'ram_org_service_enabled',
      'securityhub_org_service_enabled',
      'iam_access_analyzer_org_service_enabled',
      'config_org_service_enabled',
      'cloudformation_org_service_enabled',
      'backup_org_service_enabled',
      'infrastructure_ou_deployed',
      'security_ou_deployed',
      'workloads_ou_deployed',
      'iam_idc_org_service_enabled',
      'iam_idc_configured',
      'scp_enabled',
      'tag_policy_enabled',
      'backup_policy_enabled',
      'control_tower_deployed',
      'control_tower_latest_version',
      'control_tower_not_drifted',
      'log_archive_account_deployed',
      'audit_account_deployed'
    ];
    
    cfatRequiredWeights.forEach(weight => {
      expect(config[weight as keyof WeightConfig]).toBeDefined();
      expect(typeof config[weight as keyof WeightConfig]).toBe('number');
    });
  });
});