from pyslog.eslog2.models import (
    Invoice, BusinessEntity, Item, CEF_VAT_EXEMPTION,
    VATPointDateCode, BusinessProcessType, ItemIdentificationScheme, VATCategoryCode
)
from pyslog.eslog2.models._xml import *

def generate_eslog_invoice(
    invoice: Invoice,
    pretty_print: bool = False,
) -> str:
    eslog_buyer = ESLOG_G_SG2(
        S_NAD=ESLOG_S_NAD(
            D_3035="BY",
            C_C082=ESLOG_C_C082(
                D_3039=invoice.buyer.identifier,
                D_1131=invoice.buyer.identifier_identification_scheme_identifier
            ) if invoice.buyer.identifier else None,
            C_C080=ESLOG_C_C080(
                D_3036=invoice.buyer.name,
                D_3036_2=invoice.buyer.trading_name
            ),
            C_C059=ESLOG_C_C059(
                D_3042=invoice.buyer.address_line_1,
                D_3042_2=invoice.buyer.address_line_2,
                D_3042_3=invoice.buyer.address_line_3
            ),
            D_3207=invoice.buyer.country_code,
        ),
        G_SG3=[],
        G_SG5=[]
    )

    if invoice.buyer.vat_registration_number:
        eslog_buyer.G_SG3.append(
            ESLOG_G_SG3(
                S_RFF=ESLOG_S_RFF(
                    C_C506=ESLOG_C_C506(
                        D_1153="VA",
                        D_1154=invoice.buyer.vat_registration_number
                    )
                )
            )
        )
        eslog_buyer.G_SG3.append(
            ESLOG_G_SG3(
                S_RFF=ESLOG_S_RFF(
                    C_C506=ESLOG_C_C506(
                        D_1153="AHP",
                        D_1154=invoice.buyer.vat_registration_number
                    )
                )
            )
        )
    if invoice.buyer.maticna:
        eslog_buyer.G_SG3.append(
            ESLOG_G_SG3(
                S_RFF=ESLOG_S_RFF(
                    C_C506=ESLOG_C_C506(
                        D_1153="0199",
                        D_1154=invoice.buyer.maticna
                    )
                )
            )
        )

    if invoice.buyer.contact_person_name:
        eslog_buyer.G_SG5 = [
            ESLOG_G_SG5(
                S_CTA=ESLOG_S_CTA(
                    D_3139="BU",
                    C_C056=ESLOG_C_C056(
                        D_3412=invoice.buyer.contact_person_name
                    )
                )
            )
        ]

    if invoice.buyer.address_line_2 is not None:
        eslog_buyer.S_NAD.C_C059.D_3042_2 = invoice.buyer.address_line_2
    if invoice.buyer.address_line_3 is not None:
        eslog_buyer.S_NAD.C_C059.D_3042_3 = invoice.buyer.address_line_3
    if invoice.buyer.city is not None:
        eslog_buyer.S_NAD.D_3164 = invoice.buyer.city
    if invoice.buyer.post_code is not None:
        eslog_buyer.S_NAD.D_3251 = invoice.buyer.post_code
    if invoice.buyer.country_subdivision is not None:
        eslog_buyer.S_NAD.C_C819 = ESLOG_C_C819(
            D_3228=invoice.buyer.country_subdivision,
        )

    eslog_seller = ESLOG_G_SG2(
        S_NAD=ESLOG_S_NAD(
            D_3035="SE",
            C_C082=ESLOG_C_C082(
                D_3039=invoice.seller.identifier,
                D_1131=invoice.seller.identifier_identification_scheme_identifier
            ) if invoice.seller.identifier else None,
            C_C080=ESLOG_C_C080(
                D_3036=invoice.seller.name,
                D_3036_2=invoice.seller.trading_name
            ),
            C_C059=ESLOG_C_C059(
                D_3042=invoice.seller.address_line_1,
                D_3042_2=invoice.seller.address_line_2,
                D_3042_3=invoice.seller.address_line_3
            ),
            D_3207=invoice.seller.country_code,
        ),
        S_FII=ESLOG_S_FII(
            D_3035="RB",
            C_C078=ESLOG_C_C078(
                D_3194=invoice.seller.iban
            ),
            C_C088=ESLOG_C_C088(
                D_3433=invoice.seller.bic
            )
        ),
        G_SG3=[],
        G_SG5=[]
    )

    if invoice.seller.vat_registration_number:
        eslog_seller.G_SG3.append(
            ESLOG_G_SG3(
                S_RFF=ESLOG_S_RFF(
                    C_C506=ESLOG_C_C506(
                        D_1153="VA",
                        D_1154=invoice.seller.vat_registration_number
                    )
                )
            )
        )
        eslog_seller.G_SG3.append(
            ESLOG_G_SG3(
                S_RFF=ESLOG_S_RFF(
                    C_C506=ESLOG_C_C506(
                        D_1153="AHP",
                        D_1154=invoice.seller.vat_registration_number
                    )
                )
            )
        )
    if invoice.seller.maticna:
        eslog_seller.G_SG3.append(
            ESLOG_G_SG3(
                S_RFF=ESLOG_S_RFF(
                    C_C506=ESLOG_C_C506(
                        D_1153="0199",
                        D_1154=invoice.seller.maticna
                    )
                )
            )
        )

    if invoice.seller.contact_person_name:
        eslog_seller.G_SG5 = [
            ESLOG_G_SG5(
                S_CTA=ESLOG_S_CTA(
                    D_3139="SU",
                    C_C056=ESLOG_C_C056(
                        D_3412=invoice.seller.contact_person_name
                    )
                )
            )
        ]

    if invoice.seller.address_line_2 is not None:
        eslog_seller.S_NAD.C_C059.D_3042_2 = invoice.seller.address_line_2
    if invoice.seller.address_line_3 is not None:
        eslog_seller.S_NAD.C_C059.D_3042_3 = invoice.seller.address_line_3
    if invoice.seller.city is not None:
        eslog_seller.S_NAD.D_3164 = invoice.seller.city
    if invoice.seller.post_code is not None:
        eslog_seller.S_NAD.D_3251 = invoice.seller.post_code
    if invoice.seller.country_subdivision is not None:
        eslog_seller.S_NAD.C_C819 = ESLOG_C_C819(
            D_3228=invoice.seller.country_subdivision,
        )

    doc_field = ESLOG_S_FTX(
        D_4451="DOC",
        C_C108=ESLOG_C_C108(
            D_4440="urn:cen.eu:en16931:2017"
        )
    )
    if invoice.business_process_type is not None:
        doc_field.C_C107 = ESLOG_C_C107(
            D_4441=invoice.business_process_type.value
        )

    eslog_invoice = ESLOG_Invoice(
        M_INVOIC=ESLOG_M_INVOIC(
            Id="data",
            UNH=ESLOG_S_UNH(
                D_0062=invoice.invoice_number,  # TODO: 
                C_S009=ESLOG_C_S009(
                    D_0065="INVOIC",
                    D_0052="D",
                    D_0054="01B",
                    D_0051="UN"
                )
            ),
            BGM=ESLOG_S_BGM(
                C_C002=ESLOG_C_C002(
                    D_1001="380"  # ker je invoice
                ),
                C_C106=ESLOG_C_C106(
                    D_1004=invoice.invoice_number
                )
            ),
            DTM=[
                ESLOG_S_DTM(
                    C_C507=ESLOG_C_C507(
                        D_2005="137",
                        D_2380=invoice.invoice_issue_date
                    )
                ),
            ],
            FTX=[doc_field],
            SG1=[],
            SG2=[
                eslog_buyer,
                eslog_seller
            ],
            SG7=[
                ESLOG_G_SG7(
                    S_CUX=ESLOG_S_CUX(
                        C_C504=ESLOG_C_C504(
                            D_6347="2",
                            D_6345=invoice.reference_currency_code
                        )
                    )
                )
            ],
            SG8=[],
            SG26=[],
            UNS=ESLOG_S_UNS(
                D_0081="D"
            ),
            SG50=[
                ESLOG_G_SG50(
                    S_MOA=ESLOG_S_MOA(
                        C_C516=ESLOG_C_C516(
                            D_5025="79",
                            D_5004=invoice.sum_of_invoice_line_net_amount
                        )
                    )
                ),
                ESLOG_G_SG50(
                    S_MOA=ESLOG_S_MOA(
                        C_C516=ESLOG_C_C516(
                            D_5025="389",
                            D_5004=invoice.invoice_total_amount_without_vat
                        )
                    )
                ),
                ESLOG_G_SG50(
                    S_MOA=ESLOG_S_MOA(
                        C_C516=ESLOG_C_C516(
                            D_5025="388",
                            D_5004=invoice.invoice_total_amount_with_vat
                        )
                    )
                ),
                ESLOG_G_SG50(
                    S_MOA=ESLOG_S_MOA(
                        C_C516=ESLOG_C_C516(
                            D_5025="9",
                            D_5004=invoice.amount_due_for_payment
                        )
                    )
                ),
            
            ],
            SG52=[],
        )
    )

    for vat_item in invoice.vat_breakdown:
        eslog_tax = ESLOG_G_SG52(
            S_TAX=ESLOG_S_TAX(
                D_5283="7",
                C_C241=ESLOG_C_C241(
                    D_5153="VAT"
                ),
                C_C243=ESLOG_C_C243(
                    D_5278=vat_item.vat_category_rate
                ),
                D_5305=vat_item.vat_category_code.value
            ),
            S_MOA=[
                ESLOG_S_MOA(
                    C_C516=ESLOG_C_C516(
                        D_5025="125",
                        D_5004=vat_item.taxable_amount
                    )
                ),
                ESLOG_S_MOA(
                    C_C516=ESLOG_C_C516(
                        D_5025="124",
                        D_5004=vat_item.tax_amount
                    )
                ),
            ]
        )
        eslog_invoice.M_INVOIC.SG52.append(eslog_tax)

    for index, item in enumerate(invoice.items):
        eslog_item = ESLOG_G_SG26(
            S_LIN=ESLOG_S_LIN(
                D_1082=str(index + 1),
                C_C212=ESLOG_C_C212(
                    D_7140=item.standard_identifier,
                    D_7143=item.standard_identifier_identification_scheme_identifier,
                ),
            ),
            S_PIA=[
                ESLOG_S_PIA( ## ni nujno. Potem dodaj še en PIA za buyer identifier (segment 78)
                    D_4347="5",
                    C_C212=ESLOG_C_C212(
                        D_7140=item.sellers_item_identifier,
                        D_7143="SA",
                    ),
                )
            ],
            S_IMD=[
                ESLOG_S_IMD(  # short description
                    D_7077="F",
                    C_C273=ESLOG_C_C273(
                        D_7008=item.name
                    ),
                ),  ## TODO You can also add long description (segment 81)
            ],
            S_QTY=ESLOG_S_QTY(
                C_C186=ESLOG_C_C186(
                    D_6063="47",
                    D_6060=item.quantity,
                    D_6411=item.quantity_unit_of_measure,
                )
            ),
            S_DTM=[],
            S_FTX=[],
            G_SG27=[
                ESLOG_G_SG27(
                    S_MOA=ESLOG_S_MOA(
                        C_C516=ESLOG_C_C516(
                            D_5025="203",
                            D_5004=item.total_monetary_amount,
                        )
                    )
                ),
            ],
            G_SG29=[
                ESLOG_G_SG29(
                    S_PRI=ESLOG_S_PRI(
                        C_C509=ESLOG_C_C509(
                            D_5125="AAA",
                            D_5118=item.item_net_price,
                            D_5284=item.item_price_base_quantity,
                            D_6411=item.item_price_base_quantity_unit_of_measure_code,
                        )
                    )
                ),
            ],
            G_SG30=[],
            G_SG34=[
                ESLOG_G_SG34(
                    S_TAX=ESLOG_S_TAX(
                        D_5283="7",
                        C_C241=ESLOG_C_C241(
                            D_5153="VAT"
                        ),
                        C_C243=ESLOG_C_C243(
                            D_5278=item.vat_rate
                        ),
                        D_5305=item.vat_category_code.value,
                    ),
                    S_MOA=[

                    ]
                )
            ],
            G_SG39=[],
        )
        if item.total_monetary_amount_including_vat:
            eslog_item.G_SG27.append(
                ESLOG_G_SG27(
                    S_MOA=ESLOG_S_MOA(
                        C_C516=ESLOG_C_C516(
                            D_5025="38",
                            D_5004=item.total_monetary_amount_including_vat,
                        )
                    )
                )
            )

        if item.item_gross_price:
            eslog_item.G_SG29.append(
                ESLOG_G_SG29(
                    S_PRI=ESLOG_S_PRI(
                        C_C509=ESLOG_C_C509(
                            D_5125="AAB",
                            D_5118=item.item_gross_price,
                            D_5284=item.item_price_base_quantity,
                            D_6411=item.item_price_base_quantity_unit_of_measure_code,
                        )
                    )
                )
            )

        if item.allowance:
            eslog_item.G_SG39.append(
                ESLOG_G_SG39(
                    S_ALC=ESLOG_S_ALC(
                        D_5463="A",
                        C_C552=ESLOG_C_C552(D_5189=item.allowance.allowance_type.value)
                    ),
                    G_SG41=ESLOG_G_SG41(
                        S_PCD=ESLOG_S_PCD(
                            C_C501=ESLOG_C_C501(D_5245="1", D_5482=item.allowance.percentage)
                        )
                    ),
                    G_SG42=[
                        ESLOG_G_SG42(
                            S_MOA=ESLOG_S_MOA(
                                C_C516=ESLOG_C_C516(D_5025="204", D_5004=item.allowance.amount)
                            )
                        ),
                        ESLOG_G_SG42(
                            S_MOA=ESLOG_S_MOA(
                                C_C516=ESLOG_C_C516(D_5025="25", D_5004=item.allowance.base_amount)
                            )
                        )
                    ]
                )
            )

        eslog_invoice.M_INVOIC.SG26.append(eslog_item)

    if invoice.payment_due_date:
        eslog_invoice.M_INVOIC.SG8.append(
            ESLOG_G_SG8(
                S_PAT=ESLOG_S_PAT(D_4279="1"),
                S_DTM=[
                    ESLOG_S_DTM(
                        C_C507=ESLOG_C_C507(D_2005="13", D_2380=invoice.payment_due_date)
                    )
                ],
                S_PAI=ESLOG_S_PAI(
                    C_C534=ESLOG_C_C534(D_4461=invoice.payment_means_code.value)
                ) if invoice.payment_means_code else None
            )
        )

    if invoice.value_added_tax_point_date:
        eslog_invoice.M_INVOIC.DTM.append(
            ESLOG_S_DTM(
                C_C507=ESLOG_C_C507(D_2005="131", D_2380=invoice.value_added_tax_point_date)
            )
        )

    if invoice.value_added_tax_point_date_code:
        eslog_invoice.M_INVOIC.DTM.append(
            ESLOG_S_DTM(
                C_C507=ESLOG_C_C507(D_2005=invoice.value_added_tax_point_date_code.value)
            )
        )

    if invoice.actual_delivery_date:
        eslog_invoice.M_INVOIC.DTM.append(
            ESLOG_S_DTM(
                C_C507=ESLOG_C_C507(D_2005="35", D_2380=invoice.actual_delivery_date)
            )
        )

    if invoice.invoicing_period_start_date:
        eslog_invoice.M_INVOIC.DTM.append(
            ESLOG_S_DTM(
                C_C507=ESLOG_C_C507(D_2005="167", D_2380=invoice.invoicing_period_start_date)
            )
        )

    if invoice.invoicing_period_end_date:
        eslog_invoice.M_INVOIC.DTM.append(
            ESLOG_S_DTM(
                C_C507=ESLOG_C_C507(D_2005="168", D_2380=invoice.invoicing_period_end_date)
            )
        )

    if invoice.terms_of_payments:
        eslog_invoice.M_INVOIC.FTX.append(
            ESLOG_S_FTX(
                D_4451="AAB",
                C_C108=ESLOG_C_C108(
                    D_4440=invoice.terms_of_payments[0],
                    D_4440_2=invoice.terms_of_payments[1] if len(invoice.terms_of_payments) > 1 else None,
                    D_4440_3=invoice.terms_of_payments[2] if len(invoice.terms_of_payments) > 2 else None,
                    D_4440_4=invoice.terms_of_payments[3] if len(invoice.terms_of_payments) > 3 else None,
                    D_4440_5=invoice.terms_of_payments[4] if len(invoice.terms_of_payments) > 4 else None,
                )
            )
        )

    if invoice.seller_additional_legal_information:
        eslog_invoice.M_INVOIC.FTX.append(
            ESLOG_S_FTX(
                D_4451="AAB",
                C_C108=ESLOG_C_C108(
                    D_4440=invoice.seller_additional_legal_information
                )
            )
        )

    if invoice.invoice_note:
        eslog_invoice.M_INVOIC.FTX.append(
            ESLOG_S_FTX(
                D_4451="GEN",
                C_C108=ESLOG_C_C108(
                    D_4440=invoice.invoice_note
                )
            )
        )

    if invoice.payment_means_text:
        eslog_invoice.M_INVOIC.FTX.append(
            ESLOG_S_FTX(
                D_4451="AAT",
                C_C108=ESLOG_C_C108(
                    D_4440=invoice.payment_means_text
                )
            )
        )


    # Final sum stuff
    if invoice.sum_of_allowances_on_document_level:
        eslog_invoice.M_INVOIC.SG50.append(
            ESLOG_G_SG50(
                S_MOA=ESLOG_S_MOA(
                    C_C516=ESLOG_C_C516(
                        D_5025="260",
                        D_5004=invoice.sum_of_allowances_on_document_level
                    )
                )
            )
        )

    if invoice.sum_of_charges_on_document_level:
        eslog_invoice.M_INVOIC.SG50.append(
            ESLOG_G_SG50(
                S_MOA=ESLOG_S_MOA(
                    C_C516=ESLOG_C_C516(
                        D_5025="259",
                        D_5004=invoice.sum_of_charges_on_document_level
                    )
                )
            )
        )
    if invoice.invoice_total_vat_amount_in_accounting_currency:
        eslog_invoice.M_INVOIC.SG50.append(
            ESLOG_G_SG50(
                S_MOA=ESLOG_S_MOA(
                    C_C516=ESLOG_C_C516(
                        D_5025="2",
                        D_5004=invoice.invoice_total_vat_amount_in_accounting_currency
                    )
                )
            )
        )
    if invoice.paid_amount:
        eslog_invoice.M_INVOIC.SG50.append(
            ESLOG_G_SG50(
                S_MOA=ESLOG_S_MOA(
                    C_C516=ESLOG_C_C516(
                        D_5025="113",
                        D_5004=invoice.paid_amount
                    )
                )
            )
        )
    if invoice.rounding_amount:
        eslog_invoice.M_INVOIC.SG50.append(
            ESLOG_G_SG50(
                S_MOA=ESLOG_S_MOA(
                    C_C516=ESLOG_C_C516(
                        D_5025="366",
                        D_5004=invoice.rounding_amount
                    )
                )
            )
        )
    if invoice.invoice_total_vat_amount:
        eslog_invoice.M_INVOIC.SG50.append(
            ESLOG_G_SG50(
                S_MOA=ESLOG_S_MOA(
                    C_C516=ESLOG_C_C516(
                        D_5025="176",
                        D_5004=invoice.invoice_total_vat_amount
                    )
                )
            )
        )



    xml_string = eslog_invoice.to_xml(
        pretty_print=pretty_print,
        encoding="unicode",
    )
    return xml_string
